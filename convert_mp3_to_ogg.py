import os
import subprocess
import sys

def convert_directory(directory):
    """Convierte todos los archivos .mp3 en el directorio especificado a .ogg usando ffmpeg."""
    if not os.path.exists(directory):
        print(f"El directorio '{directory}' no existe.")
        return

    files = [f for f in os.listdir(directory) if f.lower().endswith('.mp3')]
    
    if not files:
        print(f"No se encontraron archivos .mp3 en '{directory}'.")
        return

    print(f"Encontrados {len(files)} archivos .mp3 en '{directory}'. Iniciando conversión...")

    # Verificar si ffmpeg está instalado
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Error: FFmpeg no está instalado o no se encuentra en el PATH.")
        print("Por favor instala FFmpeg para realizar la conversión.")
        return

    for filename in files:
        base_name = os.path.splitext(filename)[0]
        input_path = os.path.join(directory, filename)
        output_path = os.path.join(directory, base_name + ".ogg")
        
        print(f"Convirtiendo: {filename} -> {base_name}.ogg")
        
        try:
            # -vn: no video, -c:a libvorbis: codec ogg, -q:a 5: calidad media-alta (~160kbps)
            subprocess.run(['ffmpeg', '-i', input_path, '-vn', '-c:a', 'libvorbis', '-q:a', '5', '-y', output_path], check=True)
        except subprocess.CalledProcessError:
            print(f"❌ Error al convertir {filename}")

    print("✅ Conversión completada.")

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "audio"
    convert_directory(target_dir)