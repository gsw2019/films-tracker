--[[
    Executes for a single film title

    Lua script called by sc-im command. Looks at cell to the right for a film title. Calls Python
    script with film title as argument. Python script returns film data and here we fill it into
    respective spreadsheet cell

    @author Garret Wilson
]]


file = io.open("luascript_output.txt", "w")

json = dofile("lua/json.lua")

PYTHON_SCRIPT = "lua/python_scripts/fetch_film_data.py"

FEAT_NAMES_ROW = 2
FEAT_NAMES_START_COL = 1


function dump(o)
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


function main(c, r, mode)
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
      file:write("|" .. clean_str .. "|")
      col = col + 1
    end
  end

  -- build string of csv for feature names
  local feat_names_csv = ""
  for key,value in ipairs(feat_names) do
      feat_names_csv = feat_names_csv..value..','
  end

  -- get film title from current cursor pos
  local title = sc.lgetstr(sc.curcol(), sc.currow())

  -- call Python script and capture output
  local command = string.format('python3 %s "%s" "%s"', PYTHON_SCRIPT, feat_names_csv, title)
  file:write(command)
  file:write("\n\n")
  local handle = io.popen(command)
  if handle then
    local res = handle:read("*a")
    handle:close()

    file:write(res)

    file:write("\n")
    file:close()
  else
    file:write("Failed to run ")
    file:write(PYTHON_SCRIPT)
    file:write("\n")
    file:close()
  end

end

