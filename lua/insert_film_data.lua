--[[
    Lua script called by sc-im command.

    @author Garret Wilson
]]


file = io.open("luascript_output.txt", "w")

JSON = dofile("lua/json.lua")


-- ######################### SET VARS #########################
-- ############################################################
PYTHON_SCRIPT = "lua/python_scripts/fetch_film_data.py"

FEAT_NAMES_ROW = 2
FEAT_NAMES_START_COL = 2
-- ############################################################
-- ############################################################


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
        checks the spreadsheet for current features and stores their names

        return: 1D csv string of feature names
  ]]
  -- record feature names
  local feat_names = {}
  local col = FEAT_NAMES_START_COL
  while true do
    local val = sc.lgetstr(col, FEAT_NAMES_ROW)
    if val == nil then
      break
    else
      local clean_str = string.gsub(val, "^%s+", "")   -- from start of string ^, all whitespaces %s+, replaaced with ""
      clean_str = string.gsub(clean_str, "%s+$", "")   -- from end of string $, all whitespaces %s+, replaced with ""
      table.insert(feat_names, clean_str)
      col = col + 1
    end
  end

  -- build string of csv for feature names
  local feat_names_csv = ""
  for key,value in ipairs(feat_names) do
      feat_names_csv = feat_names_csv..value..','
  end

  return feat_names_csv, feat_names_table

end


function table_to_csv(o)
  -- TODO
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
    -- check if nested table
    if type(film_data[value]) == "table" then
      ;
    else
      local target_col = curr_col + (index - 1)
      sc.lsetstr(target_col, curr_row, film_data[value])
    end
  end


end


function main_single(c, r, mode)
  --[[
        Gets and sets data for a single film. Position of cursor is expected to be
        on target film title

        param c: column of calling cell (0 based on trigger; see ~$HOME/.config/sc-im)
        param r: row of calling cell (0 based on trigger; see ~$HOME/.config/sc-im)
        param mode: function of sc-im trigger (should be W)
  ]]
  -- get current spreadsheet feature names (column titles)
  local feat_names_csv, feat_names_table = get_features()

  -- get film title from current cursor pos
  local curr_col = sc.curcol()
  local curr_row = sc.currow()
  local title = sc.lgetstr(cur_col, cur_row)

  -- call Python script and capture output
  local command = string.format('python3 %s "%s" "%s"', PYTHON_SCRIPT, feat_names_csv, title)
  local handle = io.popen(command)
  if handle then
    local res = handle:read("*a")
    handle:close()

    local film_data = JSON.decode(res)
    write_to_sheet(curr_col, curr_row, feat_names_table, film_data)

    file:write(dump(film_data))
    file:close()

  else
    -- log command that tried to run
    file:write("--\n")
    file:write("-- [ERROR] Failed to run. Command:\n")
    file:write("-- " .. command)
    file:write("--\n")
    file:write("\n")
    file:close()
  end

end


function main_multiple(c, r, mode)
--[[
        Gets and sets data for multiple films. Position of cursor is expected to be
        on the first target film, with succcessive target films consecutively below
        the first target film. Any empty cells in between target films will stop
        execution.
  ]]

  -- TODO
end

