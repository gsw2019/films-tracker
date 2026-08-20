-- 
-- Trim leading and trailing white spaces of a cells content string
--

local file, err = io.open("luascript_output.txt", "w")
if not file then
    os.exit(1)
end

local target_col = 1  -- col B

for row = 74, 195 do
  local curr_str = sc.lgetstr(target_col, row)
  if curr_str and curr_str ~= "" then
    -- Lua global sub
    local clean_str = string.gsub(curr_str, "^%s+", "")   -- from start of string ^, all whitespaces %s+, replaaced with ""
    clean_str = string.gsub(curr_str, "%s+$", "")   -- from end of string $, all whitespaces %s+, replaced with ""
    -- file:write(clean_str)
    -- file:write("\n")
    sc.lsetstr(target_col, row, clean_str)
  end
end

file:close()

