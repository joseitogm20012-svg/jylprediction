import sys
import subprocess
from .base import BaseScraper

class FBrefScraper(BaseScraper):
    """
    Scraper integrado para los scripts de FBref (xG, xGA y disciplina).
    Ejecuta los scripts correspondientes y captura su salida en tiempo real.
    """
    
    def run(self, **kwargs):
        super().run(**kwargs)
        scraper_type = kwargs.get("type", "xg")  # "xg", "xga" o "cards"
        self.log("=" * 60)
        self.log(f"  FBref Scraper Module — {scraper_type.upper()}")
        self.log("=" * 60)
        
        if self.sandbox:
            self.log("MODO SANDBOX: Simulando extracción de datos FBref...")
            self.sleep_random(0.1, 0.3)
            
            if scraper_type == "xg":
                mock_data = [
                    {"team": "argentina", "xg_for": 2.1},
                    {"team": "brazil", "xg_for": 1.9},
                    {"team": "france", "xg_for": 2.2},
                    {"team": "germany", "xg_for": 1.8},
                    {"team": "spain", "xg_for": 2.0}
                ]
            elif scraper_type == "xga":
                mock_data = [
                    {"team": "argentina", "xg_against": 0.8},
                    {"team": "brazil", "xg_against": 0.9},
                    {"team": "france", "xg_against": 1.1},
                    {"team": "germany", "xg_against": 1.2},
                    {"team": "spain", "xg_against": 0.7}
                ]
            else:  # cards
                mock_data = [
                    {"team": "argentina", "yellow_cards": 8, "red_cards": 0},
                    {"team": "brazil", "yellow_cards": 12, "red_cards": 1},
                    {"team": "france", "yellow_cards": 9, "red_cards": 0},
                    {"team": "germany", "yellow_cards": 11, "red_cards": 2},
                    {"team": "spain", "yellow_cards": 7, "red_cards": 0}
                ]
            
            self.set_preview_data(mock_data)
            self.log(f"Simulación finalizada. {len(mock_data)} registros generados.")
            return True
            
        script_name = f"fetch_fbref_{scraper_type}.py"
        script_path = self.project_root / "data" / script_name
        
        # Verificar si el script existe en la ruta correcta
        if not script_path.exists():
            # Intentar buscar en la ruta alternativa (sin 'scripts')
            alternative_path = self.project_root / script_name
            if alternative_path.exists():
                script_path = alternative_path
            else:
                self.log(f"El script no existe en: data/{script_name} ni en la raíz del proyecto")
                return False
        
        if not script_path.exists():
            self.log(f"El script no existe en: data/{script_name}")
            return False
            
        try:
            # Ejecutar el script heredado como subproceso y redirigir la salida
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            
            # Leer stdout línea por línea
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    self.log(line.rstrip())
                    
            process.wait()
            exit_code = process.returncode
            
            if exit_code == 0:
                self.log(f"Script data/{script_name} ejecutado con éxito.")
                return True
            else:
                self.log(f"El script finalizó con código de salida: {exit_code}")
                return False
                
        except Exception as e:
            self.log(f"Error general en la ejecución del script: {str(e)}")
            return False
