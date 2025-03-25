
import os
import glob
import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from geopy.distance import geodesic


COLONY_LATITUDE = -62.21  
COLONY_LONGITUDE = -58.42  

def load_data(data_dir='./data/raw'):
    """Lädt alle CSV-Dateien aus dem Datenverzeichnis."""
    all_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    if not all_files:
        raise FileNotFoundError(f"Keine CSV-Dateien im Verzeichnis {data_dir} gefunden.")
    
    
    df_list = []
    for file in all_files:
        df = pd.read_csv(file)
        df_list.append(df)
    
    df = pd.concat(df_list, ignore_index=True)
    print(f"Daten geladen: {df.shape[0]} Zeilen und {df.shape[1]} Spalten")
    
    return df

def process_data(df):
    """Führt alle Verarbeitungsschritte durch."""
    
    df_processed = df.copy()
    
    
    
    df_processed['DateGMT'] = pd.to_datetime(df_processed['DateGMT'], format='%d/%m/%Y', errors='coerce')
    
    
    if 'TimeGMT' in df_processed.columns:
        
        df_processed[['hour', 'minute', 'second']] = df_processed['TimeGMT'].str.split(':', expand=True).astype(float)
        
        
        df_processed['Timestamp'] = df_processed.apply(
            lambda row: pd.Timestamp(
                year=row['DateGMT'].year,
                month=row['DateGMT'].month,
                day=row['DateGMT'].day,
                hour=int(row['hour']) if not pd.isna(row['hour']) else 0,
                minute=int(row['minute']) if not pd.isna(row['minute']) else 0,
                second=int(row['second']) if not pd.isna(row['second']) else 0
            ) if not pd.isna(row['DateGMT']) else pd.NaT,
            axis=1
        )
        
        
        df_processed = df_processed.drop(columns=['hour', 'minute', 'second'])
    
    
    for col in ['Latitude', 'Longitude']:
        if col in df_processed.columns:
            df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
    
    
    
    categorical_cols = ['Sex', 'Age', 'Breed Stage', 'ArgosQuality']
    for col in categorical_cols:
        if col in df_processed.columns and df_processed[col].isna().any():
            df_processed[col] = df_processed[col].fillna(df_processed[col].mode()[0])
    
    
    position_cols = ['Latitude', 'Longitude']
    if all(col in df_processed.columns for col in position_cols) and df_processed[position_cols].isna().any().any():
        imputer = KNNImputer(n_neighbors=5)
        df_processed[position_cols] = imputer.fit_transform(df_processed[position_cols])
    
    
    
    df_processed['distance_to_colony_km'] = df_processed.apply(
        lambda row: geodesic((row['Latitude'], row['Longitude']), (COLONY_LATITUDE, COLONY_LONGITUDE)).kilometers
        if not pd.isna(row['Latitude']) and not pd.isna(row['Longitude']) else np.nan,
        axis=1
    )
    
    
    if 'Timestamp' in df_processed.columns:
        df_processed['hour_of_day'] = df_processed['Timestamp'].dt.hour
        df_processed['month'] = df_processed['Timestamp'].dt.month
        
        
        season_mapping = {
            12: 'Sommer', 1: 'Sommer', 2: 'Sommer',
            3: 'Herbst', 4: 'Herbst', 5: 'Herbst',
            6: 'Winter', 7: 'Winter', 8: 'Winter',
            9: 'Frühling', 10: 'Frühling', 11: 'Frühling'
        }
        df_processed['season'] = df_processed['month'].map(season_mapping)
    
    
    
    df_processed = pd.get_dummies(df_processed, columns=categorical_cols, prefix=categorical_cols, dummy_na=True)
    
    
    print(f"Daten verarbeitet: {df_processed.shape[0]} Zeilen und {df_processed.shape[1]} Spalten")
    
    return df_processed

def save_data(df, output_path='./data/processed', filename='penguin_tracking_processed'):
    """Speichert die verarbeiteten Daten im Parquet-Format."""
    
    os.makedirs(output_path, exist_ok=True)
    
    
    parquet_path = os.path.join(output_path, f"{filename}.parquet")
    df.to_parquet(parquet_path, index=False)
    print(f"Daten als Parquet gespeichert: {parquet_path}")
     
    csv_path = os.path.join(output_path, f"{filename}.csv")
    df.to_csv(csv_path, index=False)
    print(f"Daten als CSV gespeichert: {csv_path}")

def main():
    """Hauptfunktion für die Datenverarbeitung."""
    print("Starte Datenverarbeitung")
    
    try:   
        df = load_data()
        df_processed = process_data(df) 
        save_data(df_processed)   
        print("Datenverarbeitung erfolgreich abgeschlossen")
        
    except Exception as e:
        print(f"Fehler bei der Datenverarbeitung: {e}")
        raise

if __name__ == "__main__":
    main()
