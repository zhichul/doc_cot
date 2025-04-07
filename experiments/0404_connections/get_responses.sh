export PYTHONPATH=$PYTHONPATH:$(realpath ../../)

python3 -m api.remote \
    --model meta-llama/Llama-3.3-70B-Instruct \
    --url http://nid008200:8001/v1 \
    --api_key EMPTY \
    --data_path prompts.parquet \
    --out_dir responses \
    --n_threads 16 
