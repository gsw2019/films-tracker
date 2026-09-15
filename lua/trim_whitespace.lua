-- 
-- Trim leading and trailing white spaces of a cells content string
--

-- local file, err = io.open("luascript_output.txt", "w")
-- if not file then
--     os.exit(1)
-- end


-- ######## SET VARS ##########
-- ############################
local TARGET_COL = 1  -- col B
local RANGE_START = 74
local RANGE_END = 195
-- ############################
-- ############################

for row = RANGE_START, RANGE_END do
  local curr_str = sc.lgetstr(TARGET_COL, row)
  if curr_str and curr_str ~= "" then
    -- Lua global sub
    local clean_str = string.gsub(curr_str, "^%s+", "")   -- from start of string ^, all whitespaces %s+, replaaced with ""
    clean_str = string.gsub(curr_str, "%s+$", "")   -- from end of string $, all whitespaces %s+, replaced with ""

    -- file:write(clean_str)
    -- file:write("\n")

    sc.lsetstr(TARGET_COL, row, clean_str)
  end
end

-- file:close()

