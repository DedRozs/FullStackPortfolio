from django.urls import path
from .views import PredictLSTM, PredictFinBERT, PredictRandomForest, PredictReinforcementLearning

urlpatterns = [
    path('lstm/', PredictLSTM.as_view(), name='predict-lstm'),
    path('finbert/', PredictFinBERT.as_view(), name='predict-finbert'),
    path('random_forest/', PredictRandomForest.as_view(), name='predict-random-forest'),
    path('reinforcement/', PredictReinforcementLearning.as_view(), name='predict-reinforcement'),
]
