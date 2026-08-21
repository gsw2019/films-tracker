--
-- Reads data output by a python script and inserts it into the spreadshet films.sc
--
-- @author Garret Wilson


local file = io.open("luascript_output.txt", "w")

-- local col = sc.curcol()
-- local row = sc.currow()
--
-- file:write(col)
-- file:write("\n")
-- file:write(row)
-- file:write("\n")

local str = sc.lgetstr(c, r)
file:write(str)
file:close()

