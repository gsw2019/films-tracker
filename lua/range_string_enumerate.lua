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
local RANGE_START = 196
local RANGE_END = 500

local INIT_VAL = 196
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

