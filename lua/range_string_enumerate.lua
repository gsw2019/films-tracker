-- 
-- Convert a range of a column from ints to strings
--

-- local file, err = io.open("luascript_output.txt", "w")
-- if not file then
--     os.exit(1)
-- end

-- ######## SET VARS ##########
-- ############################
local TARGET_COL = 1  -- col B
local RANGE_START = 3
local RANGE_END = 195

local INIT_VAL = 1
local STEP = 1
-- ############################
-- ############################

local val = INIT_VAL
for row = RANGE_START, RANGE_END do
    -- file:write(val)
    -- file:write("\n")

    sc.lsetstr(TARGET_COL, row, val)
    val = val + STEP
end

-- file:close()

