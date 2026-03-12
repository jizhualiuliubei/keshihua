-- ===================== 基础查询 =====================
-- 1. 基础信息：字段类型+非空数
SELECT
	count(*) AS 总记录数,
	count(日期) AS 日期非空数,
	count(销售额) AS 销售额非空数,
	count(DISTINCT 区域) AS 区域数,
	count(DISTINCT 产品类别) AS 产品类别数
FROM sales_data;

-- 2. 异常值：销量为负的记录
SELECT * 
FROM sales_data
WHERE 销量 < 0;

-- 3. 重复值：全字段重复的记录（筛查）
SELECT 日期,区域,产品类别,客户类型,销量,销售额,促销标识,备注,COUNT(*) AS 重复数
FROM sales_data
GROUP BY 日期,区域,产品类别,客户类型,销量,销售额,促销标识,备注
HAVING COUNT(*) > 1; 

-- ===================== 第一步：创建清洗后的临时表 =====================
CREATE TABLE sales_table_clean AS SELECT * FROM sales_data;

-- ===================== 第二步：去重（删除重复记录） =====================
-- 先添加自增主键（方便删除重复项）
ALTER TABLE sales_table_clean ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY;

-- 删除重复记录（保留重复组中id最小的一条）
DELETE FROM sales_table_clean
WHERE id NOT IN (
    -- 把原查询包装成派生表t，规避直接引用目标表的限制
    SELECT t.min_id FROM (
        SELECT MIN(id) AS min_id 
        FROM sales_table_clean
        GROUP BY 日期,区域,产品类别,客户类型,销量,销售额,促销标识,备注
    ) AS t
);

-- 验证去重结果（重复数应为0）
SELECT 日期,区域,产品类别,客户类型,销量,销售额,促销标识,备注,COUNT(*) AS 重复数
FROM sales_table_clean
GROUP BY 日期,区域,产品类别,客户类型,销量,销售额,促销标识,备注
HAVING COUNT(*) > 1; 

-- ===================== 第三步：异常值处理（删除销量为负的记录） =====================
-- 删除负数销量记录
DELETE FROM sales_table_clean WHERE 销量 < 0;

-- 验证异常值（结果应为空）
SELECT * FROM sales_table_clean WHERE 销量 < 0;

-- ===================== 第四步：缺失值处理（销售额为空的记录，按产品类别填充均值） =====================
-- 第一步：计算各产品类别的销售额均值
CREATE TEMPORARY TABLE temp_avg_sales AS
SELECT 产品类别, AVG(销售额) AS avg_sales
FROM sales_table_clean
WHERE 销售额 IS NOT NULL
GROUP BY 产品类别;

-- 第二步：更新缺失的销售额（按产品类别填充均值）
UPDATE sales_table_clean t1
JOIN temp_avg_sales t2 ON t1.产品类别 = t2.产品类别
SET t1.销售额 = t2.avg_sales
WHERE t1.销售额 IS NULL;

-- 验证缺失值（结果应为0）
SELECT COUNT(*) AS 销售额缺失数 FROM sales_table_clean WHERE 销售额 IS NULL;

-- ===================== 第五步：数据格式优化+新增字段 =====================
-- 1. 日期格式统一（确保为datetime类型）
ALTER TABLE sales_table_clean MODIFY COLUMN 日期 DATETIME;

-- 2. 新增「月份」字段（方便月度分析）
ALTER TABLE sales_table_clean ADD COLUMN 月份 INT;
UPDATE sales_table_clean SET 月份 = MONTH(日期);

-- 3. 促销标识转义（0=无促销，1=有促销）
ALTER TABLE sales_table_clean MODIFY COLUMN 促销标识 VARCHAR(10);
UPDATE sales_table_clean SET 促销标识 = CASE WHEN 促销标识 = '0' THEN '无促销' ELSE '有促销' END;

-- ===================== 第六步：业务分析 =====================
-- 1. 整体销售指标
SELECT
    SUM(销售额) AS 总销售额,
    SUM(销量) AS 总销量,
    AVG(销售额) AS 平均单条记录销售额
FROM sales_table_clean;

-- 2. 各区域销售额排名（降序）
SELECT 区域, SUM(销售额) AS 区域总销售额
FROM sales_table_clean
GROUP BY 区域
ORDER BY 区域总销售额 DESC;

-- 3. 促销效果分析（有/无促销的销售额对比）
SELECT
    促销标识,
    SUM(销售额) AS 促销总销售额,
    AVG(销售额) AS 促销平均销售额,
    COUNT(*) AS 订单数
FROM sales_table_clean
GROUP BY 促销标识;

-- 4. 月度销售额趋势
SELECT 月份, SUM(销售额) AS 月度总销售额
FROM sales_table_clean
GROUP BY 月份
ORDER BY 月份;

-- 5. 各产品类别销售额占比
SELECT
    产品类别,
    SUM(销售额) AS 类别总销售额,
    CONCAT(ROUND(SUM(销售额)/(SELECT SUM(销售额) FROM sales_table_clean)*100, 2), '%') AS 销售额占比
FROM sales_table_clean
GROUP BY 产品类别;

-- 6. 各客户类型的销量分布
SELECT 客户类型, SUM(销量) AS 客户类型总销量
FROM sales_table_clean
GROUP BY 客户类型;
