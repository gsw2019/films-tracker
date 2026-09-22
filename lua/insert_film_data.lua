--[[
    Lua script called by sc-im command.

    @author Garret Wilson
]]


LOG_FILE = io.open("logs/logs_lua_script.txt", "w")
LOG_CODES = {
  error = -1,
  cancelled = -2,
  no_results = -3
}

JSON = dofile("lua/json.lua")


-- ######################### SET VARS #########################
-- ############################################################
PYTHON_SCRIPT = "lua/python_scripts/fetch_film_data.py"

FEAT_NAMES_ROW = 2
FEAT_NAMES_START_COL = 2

LOG_CELL_ROW = 0
LOG_CELL_COL = 2
-- ############################################################
-- ############################################################


function write_log_delimeter()
  --[[
    Write the delimeter between films in the log file
  ]]
      LOG_FILE:write("\n\n" .. string.rep("=", 125) .. "\n" .. string.rep("=", 125) .. "\n")
      LOG_FILE:flush()
end


function dump(o)
  --[[
    build a string representation of a table

    param o: table or string
    return: string repr of table
  ]]
   if type(o) == 'table' then
      local s = '{ '
      for k,v in pairs(o) do
         local key = k
         if type(key) ~= 'number' then key = '"'..key..'"' end
         s = s .. '['..key..'] = ' .. dump(v) .. ','
      end
      return s .. '} '
   else
      return tostring(o)
   end

end


function get_features()
  --[[
    Checks the spreadsheet for current features and stores their names.
    Expected to be consecutive starting from FEAT_NAMES_ROW and FEAT_NAMES_START_COL. Only
    recordss the names until the first empty column

    return: 1D csv string of feature names
    return: table array of feature names
  ]]
  -- record feature names
  local feat_names_table = {}
  local col = FEAT_NAMES_START_COL
  while true do
    local val = sc.lgetstr(col, FEAT_NAMES_ROW)
    if val == nil then
      break
    else
      local clean_str = string.gsub(val, "^%s+", "")   -- from start of string ^, all whitespaces %s+, replaaced with ""
      clean_str = string.gsub(clean_str, "%s+$", "")   -- from end of string $, all whitespaces %s+, replaced with ""
      table.insert(feat_names_table, clean_str)
      col = col + 1
    end
  end

  -- build string of csv for feature names
  local feat_names_csv = table.concat(feat_names_table, ",")

  return feat_names_csv, feat_names_table

end


function write_to_sheet(curr_col, curr_row, feat_names_table, film_data)
  --[[
    Writes the data to the calling spreadhseet in the respective columns

    param curr_col: column position of cursor when script called
    param curr_row: row position of cursor when script called
    param feat_names_table: table preserving order of columns from spreadsheet
    param film_data: table containing film data
  ]]
  for i,film in ipairs(film_data) do
    for j,value in ipairs(feat_names_table) do
      -- skip features we dont have data for
      if film[value] == nil then
        goto continue
      end

      -- where to write to
      local target_row = curr_row + (i - 1)
      local target_col = curr_col + (j - 1)

      -- check if nested table
      if type(film[value]) == "table" then
        -- should only ever be table array
        sc.lsetstr(target_col, target_row, table.concat(film[value], ", "))
      else
        sc.lsetstr(target_col, target_row, film[value])
      end

      ::continue::
    end
  end

end


function main_single(c, r, mode)
  --[[
    Gets and sets data for a single film. Position of cursor is expected to be
    on target film title

    param c: column of calling cell (0 based on trigger; see ~$HOME/.config/sc-im)
    param r: row of calling cell (0 based on trigger; see ~$HOME/.config/sc-im)
    param mode: when trigger fires for sc-im (should be "w")
    param log_file_mode: "w" if doing a single film, "a" when being called multiple times
  ]]
  -- get film title from current cursor pos
  local curr_col = sc.curcol()
  local curr_row = sc.currow()
  local curr_title = sc.lgetstr(curr_col, curr_row)
  if curr_title == nil then
    return
  end

  LOG_FILE:write("\n-- SPREADSHEET TITLE\n")
  LOG_FILE:write("--    title: " .. curr_title .. "\n")
  LOG_FILE:flush()

  -- get current spreadsheet feature names (column titles)
  local feat_names_csv, feat_names_table = get_features()
  LOG_FILE:write("\n-- FEATURE NAMES\n")
  LOG_FILE:write("--    names: " .. feat_names_csv .. "\n")
  LOG_FILE:flush()

  -- call Python script and capture output
  local command = string.format('python3 %s -title "%s" -features "%s"', PYTHON_SCRIPT, curr_title, feat_names_csv)
  local handle = io.popen(command)

  if handle then
    local res = handle:read("*a")
    handle:close()

    -- if Python sccript gives back a log code, print message to spreadsheet and exit
    if tonumber(res) == LOG_CODES.error then
      sc.lsetstr(LOG_CELL_COL, LOG_CELL_ROW, "Error: " .. curr_title)
      write_log_delimeter()
      return
    elseif tonumber(res) == LOG_CODES.cancelled then
      sc.lsetstr(LOG_CELL_COL, LOG_CELL_ROW, "Cancelled: " .. curr_title)
      write_log_delimeter()
      return 
    elseif tonumber(res) == LOG_CODES.no_results then
      sc.lsetstr(LOG_CELL_COL, LOG_CELL_ROW, "No Results: " .. curr_title)
      write_log_delimeter()
      return 
    end

    -- protected call to avoid crashing for JSON decode failure
    local success, film_data = pcall(JSON.decode, res)

    if success then
      LOG_FILE:write("\n-- WRITING TO SPREADSHEET\n")
      LOG_FILE:write("--    film data: " .. dump(film_data) .. "\n")
      LOG_FILE:flush()
      write_to_sheet(curr_col, curr_row, feat_names_table, film_data)
    end

    if not success then
      LOG_FILE:write("\n-- [ERROR] JSON DECODE\n")
      LOG_FILE:write("--    Python output: " .. film_data .. "\n")
      LOG_FILE:flush()
    end
  else
    -- log command that tried to run
    LOG_FILE:write("\n-- [ERROR] RUN COMMAND\n")
    LOG_FILE:write("--    Command: " .. command .. "\n")
  end

  write_log_delimeter()

end


function main_multiple(c, r, mode)
--[[
    Gets and sets data for multiple films. Position of cursor is expected to be
    on the first target film, with succcessive target films consecutively below
    the first target film. Any empty cells in between target films will stop
    execution.
  ]]
  -- get title cursor is on
  local curr_row = sc.currow()
  local curr_col = sc.curcol()
  local curr_title = sc.lgetstr(curr_col, curr_row)
  if curr_title == nil then
    return
  end

  -- collect all titles
  local titles_table = {}
  local temp_curr_row = curr_row
  while curr_title ~= nil do
    table.insert(titles_table, curr_title)
    temp_curr_row = temp_curr_row + 1
    curr_title = sc.lgetstr(curr_col, temp_curr_row)
  end
  local titles_csv = table.concat(titles_table, ", ")

  -- log the titles
  LOG_FILE:write("\n-- SPREADSHEET TITLES\n")
  LOG_FILE:write("--    titles: " .. table.concat(titles_table, ", ") .. "\n")
  LOG_FILE:flush()

  -- get current spreadsheet feature names (column titles) and log the feat names
  local feat_names_csv, feat_names_table = get_features()
  LOG_FILE:write("\n-- FEATURE NAMES\n")
  LOG_FILE:write("--    names: " .. feat_names_csv .. "\n")
  LOG_FILE:flush()

  -- call Python script and capture output
  local command = string.format('python3 %s -title "%s" -features "%s"', PYTHON_SCRIPT, titles_csv, feat_names_csv)
  local handle = io.popen(command)

  if handle then
    local res = handle:read("*a")
    handle:close()

    -- if Python sccript gives back a log code, print message to spreadsheet and exit
    if tonumber(res) == LOG_CODES.error then
      sc.lsetstr(LOG_CELL_COL, LOG_CELL_ROW, "Error: " .. titles_csv)
      write_log_delimeter()
      return
    elseif tonumber(res) == LOG_CODES.cancelled then
      sc.lsetstr(LOG_CELL_COL, LOG_CELL_ROW, "Cancelled: " .. titles_csv)
      write_log_delimeter()
      return
    elseif tonumber(res) == LOG_CODES.no_results then
      sc.lsetstr(LOG_CELL_COL, LOG_CELL_ROW, "No Results: " .. titles_csv)
      write_log_delimeter()
      return
    end

    -- protected call to avoid crashing for JSON decode failure
    local success, film_data = pcall(JSON.decode, res)

    if success then
      LOG_FILE:write("\n-- WRITING TO SPREADSHEET\n")
      LOG_FILE:write("--    film data: " .. dump(film_data) .. "\n")
      LOG_FILE:flush()
      write_to_sheet(curr_col, curr_row, feat_names_table, film_data)
    end

    if not success then
      LOG_FILE:write("\n-- [ERROR] JSON DECODE\n")
      LOG_FILE:write("--    Python output: " .. film_data .. "\n")
      LOG_FILE:flush()
    end
  else
    -- log command that tried to run
    LOG_FILE:write("\n-- [ERROR] RUN COMMAND\n")
    LOG_FILE:write("--    Command: " .. command .. "\n")
  end

  write_log_delimeter()

end

