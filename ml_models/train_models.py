"""
Script to train all ML models
Run this after generating data: python ml_models/train_models.py
"""
import sys
sys.path.append('..')

from backend.models.predictive_models import VehicleFailurePredictor
import pandas as pd

def train_all_models():
    print("="*60)
    print("TorqCare ML Model Training")
    print("="*60)
    
    # Load data
    print("\n📊 Loading training data...")
    try:
        sensor_df = pd.read_csv("backend/data/sensor_data.csv")
        maintenance_df = pd.read_csv("backend/data/maintenance_history.csv")
        
        print(f"✓ Loaded {len(sensor_df)} sensor readings")
        print(f"✓ Loaded {len(maintenance_df)} maintenance records")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\n⚠ Please run data generation first:")
        print("   python backend/utils/data_generator.py")
        return
    
    # Initialize predictor
    predictor = VehicleFailurePredictor()
    
    # Train models
    print("\n🤖 Training ML models...")
    metrics = predictor.train(sensor_df, maintenance_df)
    
    # Save models
    print("\n💾 Saving trained models...")
    predictor.save_models()
    
    # Print results
    print("\n" + "="*60)
    print("✅ Training Complete!")
    print("="*60)
    print(f"Failure Prediction Accuracy: {metrics['failure_accuracy']:.2%}")
    if metrics['component_accuracy']:
        print(f"Component Classification Accuracy: {metrics['component_accuracy']:.2%}")
    print(f"RUL Estimation R² Score: {metrics['rul_r2']:.4f}")
    print("\n🎯 Models are ready for deployment!")

if __name__ == "__main__":
    train_all_models()