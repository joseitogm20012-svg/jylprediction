"""
Verificar qué ligas y competiciones internacionales están disponibles
en soccerdata para ampliar el scraper de eliminatorias.
"""
import sys
import io
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import soccerdata as sd
    print("soccerdata version:", sd.__version__)
    
    fbref = sd.FBref.__new__(sd.FBref)
    # Check available leagues
    try:
        leagues = sd.FBref._all_leagues()
        int_leagues = [(k, v) for k, v in leagues.items() if 'INT' in k or 'World' in k or 'Qual' in k or 'CONMEBOL' in k or 'UEFA' in k or 'AFC' in k or 'CONCACAF' in k or 'CAF' in k]
        print(f"\nTotal ligas: {len(leagues)}")
        print(f"\nLigas internacionales ({len(int_leagues)}):")
        for k, v in sorted(int_leagues):
            print(f"  {k:<45} -> {v}")
    except Exception as e:
        print(f"_all_leagues error: {e}")
        # Try different approach
        try:
            from soccerdata._common import LEAGUE_DICT
            int_leagues = [(k, v) for k, v in LEAGUE_DICT.items() if any(x in k for x in ['INT', 'World', 'Qual', 'CONMEBOL', 'UEFA', 'AFC', 'CONCACAF', 'CAF'])]
            print(f"\nLigas internacionales desde LEAGUE_DICT ({len(int_leagues)}):")
            for k, v in sorted(int_leagues):
                print(f"  {k:<45} -> {v}")
        except Exception as e2:
            print(f"LEAGUE_DICT error: {e2}")
            
except ImportError:
    print("soccerdata no instalado")
