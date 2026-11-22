-- 1. Monthly revenue and month-over-month growth
WITH m AS (
  SELECT substr(o.order_date,1,7) AS month, SUM(oi.qty*p.price) AS revenue
  FROM orders o JOIN order_items oi USING(order_id) JOIN products p USING(product_id)
  GROUP BY month)
SELECT month, revenue,
       ROUND(100.0*(revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month),1) AS mom_growth_pct
FROM m ORDER BY month;

-- 2. Revenue by city and category
SELECT c.city, p.category, SUM(oi.qty*p.price) AS revenue
FROM orders o JOIN customers c USING(customer_id) JOIN order_items oi USING(order_id) JOIN products p USING(product_id)
GROUP BY c.city, p.category ORDER BY revenue DESC;

-- 3. Top 10 customers by lifetime value with rank
SELECT customer_id, city, ltv, RANK() OVER (ORDER BY ltv DESC) AS rnk FROM (
  SELECT c.customer_id, c.city, SUM(oi.qty*p.price) AS ltv
  FROM customers c JOIN orders o USING(customer_id) JOIN order_items oi USING(order_id) JOIN products p USING(product_id)
  GROUP BY c.customer_id) ORDER BY rnk LIMIT 10;

-- 4. RFM segments (recency, frequency, monetary)
WITH r AS (
  SELECT o.customer_id, julianday('2026-01-01')-julianday(MAX(o.order_date)) AS recency_days,
         COUNT(DISTINCT o.order_id) AS frequency, SUM(oi.qty*p.price) AS monetary
  FROM orders o JOIN order_items oi USING(order_id) JOIN products p USING(product_id) GROUP BY o.customer_id)
SELECT CASE WHEN recency_days<=60 AND frequency>=8 THEN 'Sadık'
            WHEN recency_days<=60 THEN 'Aktif'
            WHEN recency_days<=120 THEN 'Risk altında'
            ELSE 'Kayıp' END AS segment,
       COUNT(*) AS customers, ROUND(AVG(monetary)) AS avg_value
FROM r GROUP BY segment ORDER BY avg_value DESC;

-- 5. Repeat-purchase rate
SELECT ROUND(100.0*SUM(n>1)/COUNT(*),1) AS repeat_customer_pct
FROM (SELECT customer_id, COUNT(*) AS n FROM orders GROUP BY customer_id);
