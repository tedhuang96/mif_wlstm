for lr in 1e-4 ; do
    for num_lstms in 1; do
        for hidden_size in 128; do
            for bidirectional in --bidirectional; do
                for end_mask in ""; do
                    for dataset_ver in 0 25 50 75; do
                        for compute_baseline in --compute_baseline; do
                            for eval_visual in ""; do
                            echo lr = $lr
                            echo num_lstms = $num_lstms
                            echo hidden_size = $hidden_size
                            echo dataset_ver = $dataset_ver
                            echo bidirectional = $bidirectional
                            python -u scripts/train_evaluate_wlstm.py --dataset_ver $dataset_ver --num_epochs 200 --save_epochs 50 $compute_baseline --batch_size 64 \
                                --embedding_size $hidden_size --hidden_size $hidden_size \
                                --num_layers 1 --num_lstms $num_lstms --lr $lr $bidirectional $end_mask --eval $eval_visual | tee -a logs/evaluate_wlstm.txt
                            done 
                        done
                    done
                done
            done
        done
    done
done
