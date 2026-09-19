--[[
    Lua script called by sc-im command.

    @author Garret Wilson
]]


LOG_FILE = io.open("logs_lua_script.txt", "w")
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


function write_delimeter()
  --[[
    Write the delimeter between films in the log file
  --]]
      LOG_FILE:write("\n\n" .. string.rep("=", 125) .. "\n")
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
  for index,value in ipairs(feat_names_table) do
    -- skip features we dont have data for
    if film_data[value] == nil then
      goto continue
    end

    -- where to write to
    local target_col = curr_col + (index - 1)

    -- check if nested table
    if type(film_data[value]) == "table" then
      -- should only ever be table array
      sc.lsetstr(target_col, curr_row, table.concat(film_data[value], ", "))
    else
      sc.lsetstr(target_col, curr_row, film_data[value])
    end

    ::continue::
  end

end


function main_single(c, r, mode, multiple, offset)
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
  if offset then
    curr_row = curr_row + offset
  end
  local spreadsheet_title = sc.lgetstr(curr_col, curr_row)
  if spreadsheet_title == nil then
    return -1
  end
  LOG_FILE:write("\n-- SPREADSHEET TITLE\n")
  LOG_FILE:write("--    title: " .. spreadsheet_title .. "\n")
  LOG_FILE:flush()

  -- get current spreadsheet feature names (column titles)
  local feat_names_csv, feat_names_table = get_features()
  LOG_FILE:write("\n-- FEATURE NAMES\n")
  LOG_FILE:write("--    names: " .. feat_names_csv .. "\n")
  LOG_FILE:flush()

  -- determine log file mode
  local log_file_mode = "w"
  if multiple then
    log_file_mode = "a"
  end

  -- call Python script and capture output
  local command = string.format('python3 %s "%s" "%s" %s', PYTHON_SCRIPT, feat_names_csv, spreadsheet_title, log_file_mode)
  local handle = io.popen(command)

  if handle then
    local res = handle:read("*a")
    handle:close()

    -- if Python sccript gives back a log code, print message to spreadsheet and exit
    if tonumber(res) == LOG_CODES.error then
      sc.lsetstr(LOG_CELL_COL, LOG_CELL_ROW, "Error: " .. spreadsheet_title)
      write_delimeter()
      return LOG_CODES.error
    elseif tonumber(res) == LOG_CODES.cancelled then
      sc.lsetstr(LOG_CELL_COL, LOG_CELL_ROW, "Cancelled: " .. spreadsheet_title)
      write_delimeter()
      return LOG_CODES.cancelled
    elseif tonumber(res) == LOG_CODES.no_results then
      sc.lsetstr(LOG_CELL_COL, LOG_CELL_ROW, "No Results: " .. spreadsheet_title)
      write_delimeter()
      return LOG_CODES.no_results
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

  write_delimeter()

  -- only time main_single handles closing the log file
  if not multiple then
    LOG_FILE:close()
  end

  return 0, spreadsheet_title

end


function main_multiple(c, r, mode)
--[[
    Gets and sets data for multiple films. Position of cursor is expected to be
    on the first target film, with succcessive target films consecutively below
    the first target film. Any empty cells in between target films will stop
    execution.
  ]]

  -- clear python logs for new batch
  local python_logs = io.open("logs_python_script.txt", "w")
  python_logs:close()

  local offset = 0
  while true do
    local status, spreadsheet_title = main_single(c, r, mode, true, offset)
    if status == 1 or status == LOG_CODES.error or status == LOG_CODES.cancelled then
      LOG_FILE:close()
      return
    elseif status == 0 or status == LOG_CODES.no_results then
      sc.redraw()
      offset = offset + 1
    end
  end

end

