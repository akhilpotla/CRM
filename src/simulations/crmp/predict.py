import pandas as pd

from src.config import INPUTS
from src.data.read_crmp import (injectors, net_productions, producers,
     producer_names)
from src.helpers.cross_validation import forward_walk_splitter
from src.helpers.features import net_production_dataset, production_rate_dataset
from src.helpers.models import load_models, model_namer, test_model
from src.simulations import number_of_producers, step_sizes


# Loading the previously serialized models
trained_models = load_models('crmp')

# Loading the production rate models up by producer
production_rate_models_by_producer = {}
for producer in producer_names:
    producer_label = producer.lower().replace(' ', '_')
    keys_for_producer = []
    for key in trained_models.keys():
        if producer_label in key and 'net_' not in key:
            keys_for_producer.append(key)
    production_rate_models_by_producer[producer] = [trained_models[key] for key in keys_for_producer]

# Predict each producer with each model
q_predictions_file = INPUTS['crmp']['q_predictions']
q_predictions_metrics_file = INPUTS['crmp']['q_predictions_metrics']
predictions_data = {
    'Producer': [], 'Model': [], 'Step size': [], 't_start': [], 't_end': [],
    't_i': [], 'Prediction': []
}
metrics_data = {
    'Producer': [], 'Model': [], 'Step size': [], 'r2': [], 'MSE': []
}
for i in range(number_of_producers):
    producer_name = producer_names[i]
    producer_number = i + 1
    models = production_rate_models_by_producer[producer_name]
    X, y = production_rate_dataset(producers[i], *injectors)

    for model in models:
        for step_size in step_sizes:
            test_split = forward_walk_splitter(X, y, step_size)[1]
            r2, mse, y_hat, time_step = test_model(X, y, model, test_split)
            metrics_data['Producer'].append(producer_number)
            metrics_data['Model'].append(model_namer(model))
            metrics_data['Step size'].append(step_size)
            metrics_data['r2'].append(r2)
            metrics_data['MSE'].append(mse)
            for i in range(len(y_hat)):
                y_hat_i = y_hat[i]
                time_step_i = time_step[i]
                t_start = time_step_i[0] + 2
                t_end = time_step_i[-1] + 2
                for k in range(len(y_hat_i)):
                    y_i = y_hat_i[k]
                    t_i = time_step_i[k] + 2
                    predictions_data['Producer'].append(producer_number)
                    predictions_data['Model'].append(model_namer(model))
                    predictions_data['Step size'].append(step_size)
                    predictions_data['t_start'].append(t_start)
                    predictions_data['t_end'].append(t_end)
                    predictions_data['t_i'].append(t_i)
                    predictions_data['Prediction'].append(y_i)

metrics_df = pd.DataFrame(metrics_data)
metrics_df.to_csv(q_predictions_metrics_file)
predictions_df = pd.DataFrame(predictions_data)
predictions_df.to_csv(q_predictions_file)
