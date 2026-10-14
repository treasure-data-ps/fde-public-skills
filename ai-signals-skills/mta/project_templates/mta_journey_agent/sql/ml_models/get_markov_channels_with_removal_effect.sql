SELECT column_name FROM INFORMATION_SCHEMA.columns 
WHERE table_schema = '${sink_database}' AND table_name = 'mta_markov_transition' 
AND column_name IN (SELECT DISTINCT lower(REGEXP_REPLACE(channels, '-| ', '_')) FROM mta_markov_attribution WHERE removal_effect > ${removal_effect_limit})

