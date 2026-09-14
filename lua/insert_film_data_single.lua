--[[
    Executes for a single film title

    Lua script called by sc-im command. Looks at cell to the right for a film title. Calls Python
    script with film title as argument. Python script returns film data and here we fill it into
    respective spreadsheet cell

    @author Garret Wilson
]]

-- local file = io.open("luascript_output.txt", "w")

-- local PYTHON_SCRIPT = "lua/python_scripts/fetch_film_data.py"
--
-- local COL_NAMES_ROW = 2
-- local COL_NAMES_COL_START = 1
-- local COL_NAMES_COL_END = 14
--
-- local ACTION_COL_OFFSET = 1
--
-- -- record column names
-- local column_names = {}
-- for i = COL_NAMES_COL_START, COL_NAMES_COL_END do
--   -- table.insert(column_names, sc.lgetstr(i, COL_NAMES_ROW))
-- end
--
-- -- get film title
-- local title = sc.lgetstr(c + ACTION_COL_OFFSET, r)
--
-- -- call Python script and capture output
-- local command = string.format('python3 %s "%s"', PYTHON_SCRIPT, title)
-- file:write(command)
-- file:write("\n")
-- local handle = io.popen(command)
-- if handle then
--   local res = handle:read("*a")
--   handle:close()
--   file:write(res)
--   file:write("\n")
--   file:close()
-- else
--   file:write("Failed to run ")
--   file:write(PYTHON_SCRIPT)
--   file:write("\n")
--   file:close()
-- end

function main(c, r, mode)
  local file = io.open("luascript_output.txt", "w")
  file:write("fired\n")
  file:write(tostring(sc.curcol()))
  file:write(" ")
  file:write(tostring(sc.currow()))
  file:close()
end

