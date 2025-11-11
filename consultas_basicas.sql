-- CONSULTAS BÁSICAS - SENSORES_FASE2
-- Mostra 20 linhas de amostra (confirmação de carga)
SELECT *
FROM SENSORES_FASE2
FETCH FIRST 20 ROWS ONLY;

-- Médias diárias de variáveis principais
SELECT
  TRUNC(DATA_COLETA)                    AS DIA,
  ROUND(AVG(UMIDADE_SOLO), 2)           AS AVG_UMID,
  ROUND(AVG(PH_SOLO), 2)                AS AVG_PH,
  ROUND(AVG(FOSFORO_P), 2)              AS AVG_P,
  ROUND(AVG(POTASSIO_K), 2)             AS AVG_K
FROM SENSORES_FASE2
GROUP BY TRUNC(DATA_COLETA)
ORDER BY DIA;

-- pH fora da faixa ideal (5.5 a 7.5) – últimas leituras primeiro
SELECT *
FROM SENSORES_FASE2
WHERE PH_SOLO < 5.5 OR PH_SOLO > 7.5
ORDER BY DATA_COLETA DESC;

-- (Opcional) Quantidade total de registros
SELECT COUNT(*) AS TOTAL_REGISTROS
FROM SENSORES_FASE2;
