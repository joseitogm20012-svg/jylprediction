import re

with open("C:/Users/Equipo/Desktop/predecirv2/app.js", "r", encoding="utf-8") as f:
    content = f.read()

# Define the new TEAM_METADATA dictionary in JS
new_metadata_js = """const TEAM_METADATA = {
  "argentina": { name: "Argentina", flag: "ARG", rank: 1 },
  "france": { name: "Francia", flag: "FRA", rank: 3 },
  "spain": { name: "España", flag: "ESP", rank: 2 },
  "brazil": { name: "Brasil", flag: "BRA", rank: 6 },
  "england": { name: "Inglaterra", flag: "ENG", rank: 4 },
  "portugal": { name: "Portugal", flag: "POR", rank: 5 },
  "netherlands": { name: "Países Bajos", flag: "NED", rank: 8 },
  "germany": { name: "Alemania", flag: "GER", rank: 10 },
  "austria": { name: "Austria", flag: "AUT", rank: 24 },
  "belgium": { name: "Bélgica", flag: "BEL", rank: 9 },
  "italy": { name: "Italia", flag: "ITA", rank: 12 },
  "colombia": { name: "Colombia", flag: "COL", rank: 13 },
  "croatia": { name: "Croacia", flag: "CRO", rank: 11 },
  "morocco": { name: "Marruecos", flag: "MAR", rank: 7 },
  "usa": { name: "Estados Unidos", flag: "USA", rank: 17 },
  "switzerland": { name: "Suiza", flag: "SUI", rank: 19 },
  "uruguay": { name: "Uruguay", flag: "URU", rank: 16 },
  "japan": { name: "Japón", flag: "JPN", rank: 18 },
  "mexico": { name: "México", flag: "MEX", rank: 14 },
  "senegal": { name: "Senegal", flag: "SEN", rank: 15 },
  "denmark": { name: "Dinamarca", flag: "DEN", rank: 21 },
  "iran": { name: "Irán", flag: "IRN", rank: 20 },
  "ecuador": { name: "Ecuador", flag: "ECU", rank: 23 },
  "australia": { name: "Australia", flag: "AUS", rank: 27 },
  "south-korea": { name: "Corea del Sur", flag: "KOR", rank: 25 },
  "poland": { name: "Polonia", flag: "POL", rank: 36 },
  "wales": { name: "Gales", flag: "WAL", rank: 38 },
  "nigeria": { name: "Nigeria", flag: "NGA", rank: 26 },
  "peru": { name: "Perú", flag: "PER", rank: 52 },
  "serbia": { name: "Serbia", flag: "SRB", rank: 43 },
  "qatar": { name: "Catar", flag: "QAT", rank: 56 },
  "czech-republic": { name: "República Checa", flag: "CZE", rank: 40 },
  "egypt": { name: "Egipto", flag: "EGY", rank: 29 },
  "ivory-coast": { name: "Costa de Marfil", flag: "CIV", rank: 33 },
  "scotland": { name: "Escocia", flag: "SCO", rank: 42 },
  "canada": { name: "Canadá", flag: "CAN", rank: 30 },
  "tunisia": { name: "Túnez", flag: "TUN", rank: 45 },
  "chile": { name: "Chile", flag: "CHI", rank: 51 },
  "algeria": { name: "Argelia", flag: "ALG", rank: 28 },
  "panama": { name: "Panamá", flag: "PAN", rank: 34 },
  "cameroon": { name: "Camerún", flag: "CMR", rank: 45 },
  "jamaica": { name: "Jamaica", flag: "JAM", rank: 71 },
  "venezuela": { name: "Venezuela", flag: "VEN", rank: 48 },
  "paraguay": { name: "Paraguay", flag: "PAR", rank: 41 },
  "south-africa": { name: "Sudáfrica", flag: "RSA", rank: 60 },
  "saudi-arabia": { name: "Arabia Saudita", flag: "KSA", rank: 61 },
  "ghana": { name: "Ghana", flag: "GHA", rank: 73 },
  "jordan": { name: "Jordania", flag: "JOR", rank: 63 },
  "bosnia-and-herzegovina": { name: "Bosnia & Herzegovina", flag: "BIH", rank: 64 },
  "honduras": { name: "Honduras", flag: "HON", rank: 65 },
  "el-salvador": { name: "El Salvador", flag: "SLV", rank: 100 },
  "new-zealand": { name: "Nueva Zelanda", flag: "NZL", rank: 85 },
  "haiti": { name: "Haití", flag: "HAI", rank: 83 },
  "trinidad-and-tobago": { name: "Trinidad y Tobago", flag: "TRI", rank: 102 },
  "guatemala": { name: "Guatemala", flag: "GUA", rank: 97 },
  "norway": { name: "Noruega", flag: "NOR", rank: 31 },
  "sweden": { name: "Suecia", flag: "SWE", rank: 38 },
  "turkey": { name: "Turquía", flag: "TUR", rank: 27 },
  "uae": { name: "Emiratos Árabes Unidos", flag: "UAE", rank: 68 },
  "iraq": { name: "Irak", flag: "IRQ", rank: 57 },
  "cape-verde": { name: "Cabo Verde", flag: "CPV", rank: 67 },
  "dr-congo": { name: "República Dem. del Congo", flag: "COD", rank: 43 },
  "curacao": { name: "Curazao", flag: "CUW", rank: 82 }
};"""

# Replace TEAM_METADATA block in app.js
pattern = r'const TEAM_METADATA = \{[\s\S]*?\};'
updated_content, count = re.subn(pattern, new_metadata_js, content)

if count > 0:
    with open("C:/Users/Equipo/Desktop/predecirv2/app.js", "w", encoding="utf-8") as f:
        f.write(updated_content)
    print("Success: TEAM_METADATA replaced.")
else:
    print("Error: TEAM_METADATA not found.")
