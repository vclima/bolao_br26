#!/usr/bin/env python3
"""
Brazilian Soccer Championship 2026 Classification Scraper
Compares actual standings with player predictions and calculates scores.
"""

import json
import os
import urllib.request
import urllib.parse
import ssl
import re
from datetime import datetime
import base64
import unicodedata

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class BrasileiroScraper:
    def __init__(self):
        # Create SSL context that doesn't verify certificates (for testing)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def load_predictions(self, json_file="bolao.json"):
        """Load player predictions from JSON file"""
        try:
            if not os.path.exists(json_file):
                print(f"Predictions file not found: {json_file}")
                return None
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
        except Exception as e:
            print(f"Error loading predictions: {e}")
            return None
    
    def fetch_url(self, url):
        """Fetch URL content"""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, context=self.ssl_context) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def scrape_espn_standings(self, team_match_map=None):
        """Scrape standings from ESPN Brazil"""
        url = "https://www.espn.com.br/futebol/liga/_/nome/bra.1"
        
        print("Fetching standings from ESPN Brazil...")
        html_content = self.fetch_url(url)
        
        if not html_content:
            return None
        
        # Parse the HTML to extract standings
        teams = []
        
        # Look for table rows with team data using regex
        # This is a simplified approach - finding table rows
        table_pattern = r'<tr[^>]*>.*?</tr>'
        rows = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        position = 1
        for row in rows:
            # Skip header rows
            if 'th>' in row or 'header' in row.lower():
                continue
            
            # Look for team names - ESPN typically has team names in links or specific classes
            team_name = None
            anchor_texts = re.findall(r'<a[^>]*>([^<]+)</a>', row, re.IGNORECASE)
            for anchor_text in anchor_texts:
                candidate = re.sub(r'\s+', ' ', anchor_text).strip()
                if not candidate:
                    continue
                candidate_key = self.normalize_team_key(candidate)
                if not team_match_map or candidate_key in team_match_map:
                    team_name = team_match_map.get(candidate_key, candidate) if team_match_map else candidate
                    break

            if team_name:
                # Clean up team name
                team_name = re.sub(r'\s+', ' ', team_name)
                
                # Extract points/stats from the row
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL | re.IGNORECASE)
                
                if len(cells) >= 5:  # Minimum columns expected
                    # Clean cell content
                    clean_cells = []
                    for cell in cells:
                        clean_text = re.sub(r'<[^>]+>', '', cell).strip()
                        clean_cells.append(clean_text)
                    
                    # Try to find games played (usually 2nd or 3rd column)
                    games_played = '0'
                    for i, cell in enumerate(clean_cells[1:4]):  # Check columns 1-3
                        if cell.isdigit() and 0 <= int(cell) <= 38:  # Valid range for games in Brasileirão
                            games_played = cell
                            break
                    
                    teams.append({
                        'position': position,
                        'team': team_name,
                        'points': clean_cells[-1] if clean_cells else '0',  # Points usually last column
                        'games': games_played
                    })
                    position += 1
                    
                    if position > 20:  # Brasileirão has 20 teams
                        break
        
        return teams if teams else None
    
    def scrape_gazeta_standings(self, team_match_map=None):
        """Scrape standings from Gazeta Esportiva"""
        url = "https://www.gazetaesportiva.com/campeonatos/brasileiro-serie-a/"
        
        print("Fetching standings from Gazeta Esportiva...")
        html_content = self.fetch_url(url)
        
        if not html_content:
            return None
        
        teams = []
        
        # Encontrar a tabela principal
        table_match = re.search(r'<table[^>]*>.*?</table>', html_content, re.DOTALL)
        
        if table_match:
            table = table_match.group(0)
            
            # Extrair todas as linhas da tabela
            rows = re.findall(r'<tr[^>]*>.*?</tr>', table, re.DOTALL)
            
            position = 1
            for i, row in enumerate(rows):
                # Pular cabeçalho
                if '<th>' in row or i == 0:
                    continue
                
                # Extrair células
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                
                if len(cells) >= 3:  # Pelo menos posição, time, pontos
                    # Limpar conteúdo das células
                    clean_cells = []
                    for cell in cells:
                        clean_text = re.sub(r'<[^>]+>', '', cell).strip()
                        clean_text = re.sub(r'\s+', ' ', clean_text)
                        clean_cells.append(clean_text)
                    
                    # Tentar encontrar nome do time
                    team_name = None
                    if team_match_map:
                        for cell in clean_cells:
                            cell_key = self.normalize_team_key(cell)
                            for team_key, canonical in team_match_map.items():
                                if team_key and team_key in cell_key:
                                    team_name = canonical
                                    break
                            if team_name:
                                break
                    else:
                        for cell in clean_cells:
                            if cell:
                                team_name = cell
                                break
                    
                    # Encontrar pontos (último número válido na linha)
                    points = '0'
                    games_played = '0'
                    
                    for cell in reversed(clean_cells):
                        if cell.isdigit():
                            num = int(cell)
                            if num <= 114:  # Máximo de pontos possível no Brasileirão
                                points = cell
                                break
                    
                    # Tentar encontrar jogos (número entre 0-38)
                    for cell in clean_cells:
                        if cell.isdigit():
                            num = int(cell)
                            if 0 <= num <= 38:  # Número válido de jogos
                                games_played = cell
                                break
                    
                    if team_name:
                        # Normalizar nome do time para compatibilidade
                        team_name = self.normalize_team_name(team_name)
                        
                        teams.append({
                            'position': position,
                            'team': team_name,
                            'points': points,
                            'games': games_played
                        })
                        
                        position += 1
                        
                        if position > 20:
                            break
        
        return teams if teams else None
    
    def get_current_standings(self, team_match_map=None):
        """Get current standings by scraping from online sources"""
        print("Scraping current Brazilian Championship 2026 standings...")
        
        # Try multiple sources in order of reliability
        sources = [
            ("ESPN Brazil", lambda: self.scrape_espn_standings(team_match_map)),
            ("Gazeta Esportiva", lambda: self.scrape_gazeta_standings(team_match_map)),
        ]
        
        for source_name, scraper_func in sources:
            try:
                standings = scraper_func()
                if standings and len(standings) >= 15:  # At least 15 teams found
                    print(f"✅ Successfully scraped {len(standings)} teams from {source_name}")
                    return standings
                else:
                    print(f"❌ {source_name}: Insufficient data ({len(standings) if standings else 0} teams)")
            except Exception as e:
                print(f"❌ {source_name}: Error - {e}")
        
        # No fallback - if scraping fails, return None
        print("❌ All scraping sources failed")
        return None
    
    def normalize_team_name(self, team_name):
        """Normalize team names to match predictions"""
        # Clean up the team name
        team_name = team_name.strip()
        
        # Handle common variations
        name_mappings = {
            'Red Bull Bragantino': 'Bragantino',
            'RB Bragantino': 'Bragantino',
            'Vasco da Gama': 'Vasco',
            'Atlético-MG': 'Atlético-MG',
            'Atlético Mineiro': 'Atlético-MG',
            'Atletico-MG': 'Atlético-MG',
            'Athletico-PR': 'Atlético-PR',
            'Athletico Paranaense': 'Atlético-PR',
            'Atlético-PR': 'Atlético-PR',
            'Atletico-PR': 'Atlético-PR',
            'Red Bull Salzburg': 'Bragantino',  # Just in case
            'Sao Paulo': 'São Paulo',
            'Sao-Paulo': 'São Paulo',
            'Vitoria': 'Vitória',
            'Gremio': 'Grêmio',
        }
        
        # Check direct mappings
        if team_name in name_mappings:
            return name_mappings[team_name]
        
        # Check if any mapping key contains the team name or vice versa
        for key, value in name_mappings.items():
            if key.lower() in team_name.lower() or team_name.lower() in key.lower():
                return value
        
        return team_name

    def normalize_team_key(self, text):
        """Normalize text for matching team names"""
        text = text.strip().lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        text = re.sub(r"\s+", " ", text)
        return text

    def get_teams_from_predictions(self, predictions):
        """Extract unique team names from predictions"""
        teams = set()
        if not predictions:
            return teams
        for player_predictions in predictions.values():
            for team in player_predictions.values():
                if team:
                    teams.add(team)
        return teams

    def build_team_match_map(self, teams):
        """Build a map of normalized team variants to canonical team names"""
        team_match_map = {}

        variant_map = {
            'Bragantino': ['Red Bull Bragantino', 'RB Bragantino'],
            'Vasco': ['Vasco da Gama'],
            'Atlético-MG': ['Atlético Mineiro', 'Atletico-MG'],
            'Atlético-PR': ['Athletico-PR', 'Athletico Paranaense', 'Atletico-PR'],
            'São Paulo': ['Sao Paulo', 'Sao-Paulo'],
            'Vitória': ['Vitoria'],
            'Grêmio': ['Gremio'],
        }

        for team in teams:
            team_key = self.normalize_team_key(team)
            if team_key:
                team_match_map[team_key] = team

            for variant in variant_map.get(team, []):
                variant_key = self.normalize_team_key(variant)
                if variant_key:
                    team_match_map[variant_key] = team

        return team_match_map
    
    def calculate_score(self, predicted_pos, actual_pos):
        """Calculate score: 20 points minus absolute deviation"""
        deviation = abs(predicted_pos - actual_pos)
        score = max(0, 20 - deviation)  # Minimum score is 0
        return score
    
    def compare_predictions(self, actual_standings, predictions):
        """Compare predictions with actual standings and calculate scores"""
        if not predictions or not actual_standings:
            return
        
        # Calculate scores for each player
        player_scores = {}
        raw_scores = {}

        # Initialize raw scores for all players
        for player in predictions.keys():
            raw_scores[player] = 0
        
        print(f"\n🏆 BRASILEIRÃO 2026 - BOLÃO RESULTS")
        print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 120)
        
        # Header
        print(f"{'Team':<20} {'Actual':<8}", end="")
        for player in predictions.keys():
            print(f"{player:<12}", end="")
        print()
        print("-" * 120)
        
        # Process each team
        for team_data in actual_standings:
            original_team_name = team_data['team']
            team_name = self.normalize_team_name(original_team_name)
            actual_pos = team_data['position']
            
            print(f"{original_team_name:<20} {actual_pos:<8}", end="")
            
            for player, player_predictions in predictions.items():
                # Find predicted position for this team
                predicted_pos = None
                for pos, predicted_team in player_predictions.items():
                    if predicted_team == team_name:
                        predicted_pos = int(pos)
                        break
                if predicted_pos is not None:
                    score = self.calculate_score(predicted_pos, actual_pos)
                    raw_scores[player] += score
                    print(f"{predicted_pos}°({score}p) ", end="")
                else:
                    print("--       ", end="")
            
            print()

        # Bonus points: 3 points for correct 1st place and 3 points for hitting 3 of the last 4
        actual_by_position = {}
        for team_data in actual_standings:
            try:
                position = int(team_data.get('position'))
            except (TypeError, ValueError):
                continue
            actual_by_position[position] = self.normalize_team_name(team_data.get('team', ''))

        actual_first_team = actual_by_position.get(1)
        actual_bottom_four = {
            actual_by_position.get(17),
            actual_by_position.get(18),
            actual_by_position.get(19),
            actual_by_position.get(20),
        }
        actual_bottom_four.discard(None)

        for player, player_predictions in predictions.items():
            # Champion bonus
            predicted_first_team = player_predictions.get('1') or player_predictions.get(1)
            if predicted_first_team:
                predicted_first_team = self.normalize_team_name(predicted_first_team)
            if actual_first_team and predicted_first_team == actual_first_team:
                raw_scores[player] += 3

            # Bottom four bonus (3 or more correct among positions 17-20)
            predicted_bottom_four = set()
            for pos in range(17, 21):
                predicted_team = player_predictions.get(str(pos)) or player_predictions.get(pos)
                if predicted_team:
                    predicted_bottom_four.add(self.normalize_team_name(predicted_team))

            if actual_bottom_four and len(predicted_bottom_four.intersection(actual_bottom_four)) >= 3:
                raw_scores[player] += 3
        
        # Display final scores
        print("-" * 120)
        print(f"{'FINAL SCORES:':<20} {'':>8}", end="")
        player_scores = {}
        for player in predictions.keys():
            norm_score = max(0, min(100, round((raw_scores.get(player, 0) - 200) / 2)))
            player_scores[player] = norm_score
            print(f"{norm_score:<12}", end="")
        print()
        # Retorna também os scores brutos para uso na tabela do README
        return player_scores, raw_scores
    

    def get_current_round(self, standings):
        """Calculate last completed round based on maximum games played by any team"""
        if not standings:
            return 1
        
        max_games = 0
        games_found = False
        
        for team_data in standings:
            try:
                games = team_data.get('games', '0')
                if games and games != '0':
                    games_int = int(games)
                    max_games = max(max_games, games_int)
                    games_found = True
            except (ValueError, TypeError):
                continue
        
        # If no valid game data found, assume early in season (round 1)
        if not games_found or max_games == 0:
            print("⚠️ Dados de jogos não encontrados - assumindo início da temporada (Rodada 1)")
            return 1
        
        # Return the last completed round (maximum games played)
        return max_games

    def save_score_history(self, normalized_scores, raw_scores, current_round, force_update=False):
        """Save current scores to history for graph generation"""
        history_file = "score_history.json"
        
        try:
            # Load existing history
            history = []
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    try:
                        history = json.load(f)
                    except json.JSONDecodeError:
                        print("⚠️ score_history.json inválido ou vazio - reiniciando histórico")
                        history = []
            
            # Create new entry
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_entry = {
                'timestamp': timestamp,
                'round': current_round,
                'normalized_scores': normalized_scores,
                'raw_scores': raw_scores
            }
            
            # Check if scores have changed from last entry
            scores_changed = True
            should_add_to_history = True
            
            if history and len(history) > 0:
                last_entry = history[-1]
                
                # Check if normalized scores are the same
                if last_entry.get('normalized_scores') == normalized_scores:
                    scores_changed = False
                    
                    # If force_update, update the timestamp of the last entry instead of adding new
                    if force_update:
                        print("📊 Scores unchanged but force updating - refreshing timestamp")
                        history[-1]['timestamp'] = timestamp
                        should_add_to_history = False
                    else:
                        print("📊 Scores unchanged - not adding to history")
                        should_add_to_history = False
            
            # Add new entry only if scores actually changed
            if should_add_to_history and scores_changed:
                history.append(new_entry)
                print(f"📈 Score history updated: Rodada {current_round} - {timestamp}")
            
            # Save updated history (either new entry or updated timestamp)
            if should_add_to_history or (force_update and not scores_changed):
                with open(history_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)
            
            # Always return True if we need to update graph (either scores changed or force update)
            return scores_changed or force_update
            
        except Exception as e:
            print(f"❌ Error saving score history: {e}")
            return False

    def filter_unique_rounds(self, history):
        """Filter history to keep only the latest entry for each round"""
        if not history:
            return []
        
        # Create a dictionary to store the latest entry for each round
        unique_rounds = {}
        
        for entry in history:
            round_num = entry.get('round', 0)
            timestamp = entry.get('timestamp', '')
            
            # Keep the entry with the latest timestamp for each round
            if round_num not in unique_rounds or timestamp > unique_rounds[round_num]['timestamp']:
                unique_rounds[round_num] = entry
        
        # Convert back to list and sort by round number
        filtered_history = list(unique_rounds.values())
        filtered_history.sort(key=lambda x: x.get('round', 0))
        
        return filtered_history

    def generate_score_graph(self):
        """Generate visual score graph for README"""
        history_file = "score_history.json"
        
        if not os.path.exists(history_file):
            return ["", "### 📈 Histórico de Desempenho", "", "*Nenhum histórico disponível ainda.*", ""]
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                try:
                    full_history = json.load(f)
                except json.JSONDecodeError:
                    return ["", "### 📈 Histórico de Desempenho", "", "*Histórico inválido ou vazio.*", ""]
            
            if not full_history:
                return ["", "### 📈 Histórico de Desempenho", "", "*Nenhum histórico disponível ainda.*", ""]
            
            # Filter to get only the latest entry for each round
            history = self.filter_unique_rounds(full_history)
            
            # Get player names from latest entry and sort by current score (descending)
            latest_entry = history[-1]
            players_scores = [(player, score) for player, score in latest_entry['normalized_scores'].items()]
            players_scores.sort(key=lambda x: x[1], reverse=True)  # Sort by score descending
            players = [player for player, score in players_scores]
            
            graph_lines = []
            graph_lines.append("")
            graph_lines.append("### 📈 Histórico de Desempenho")
            graph_lines.append("")
            
            # Generate visual chart if matplotlib is available
            if MATPLOTLIB_AVAILABLE and len(history) >= 1:
                try:
                    self.create_performance_chart(history, players)
                    graph_lines.append("![Gráfico de Performance](performance_chart.png)")
                    graph_lines.append("")
                except Exception as e:
                    print(f"⚠️ Warning: Could not generate chart: {e}")
            
            # Create a simple ASCII table showing score progression
            if len(history) >= 1:
                # Table header with players ordered by current score
                header = "| Rodada | " + " | ".join([f"{player}" for player in players]) + " |"
                separator = "|" + "|".join(["-------"] * (len(players) + 1)) + "|"
                
                graph_lines.append(header)
                graph_lines.append(separator)
                
                # Show last 10 unique rounds to keep table manageable
                recent_history = history[-10:]
                
                for entry in recent_history:
                    round_num = entry.get('round', 'N/A')
                    
                    row = f"| R{round_num} |"
                    for player in players:  # Use ordered players
                        score = entry['normalized_scores'].get(player, 0)
                        row += f" {score} |"
                    
                    graph_lines.append(row)
                
                # Add trend indicators
                graph_lines.append("")
                graph_lines.append("**Tendência (últimas 2 medições):**")
                
                if len(history) >= 2:
                    current = history[-1]['normalized_scores']
                    previous = history[-2]['normalized_scores']
                    
                    trends = []
                    for player in players:  # Use ordered players
                        current_score = current.get(player, 0)
                        previous_score = previous.get(player, 0)
                        diff = current_score - previous_score
                        
                        if diff > 0:
                            trend = f"📈 +{diff}"
                        elif diff < 0:
                            trend = f"📉 {diff}"
                        else:
                            trend = "➡️ =0"
                        
                        trends.append(f"**{player}**: {trend}")
                    
                    graph_lines.extend([f"- {trend}" for trend in trends])
                
            else:
                graph_lines.append("*Aguardando mais dados para mostrar histórico...*")
            
            graph_lines.append("")
            
            return graph_lines
            
        except Exception as e:
            print(f"❌ Error generating score graph: {e}")
            return ["", "### 📈 Histórico de Desempenho", "", f"*Erro ao gerar gráfico: {e}*", ""]

    def create_performance_chart(self, history, players):
        """Create a visual performance chart using matplotlib"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Configure matplotlib for better appearance
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Colors for each player
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        # Prepare data - use rounds instead of timestamps
        rounds = []
        for entry in history:
            # Get round from entry, or estimate from position if not available
            round_num = entry.get('round', len(rounds) + 1)
            rounds.append(round_num)
        
        # Plot lines for each player
        for i, player in enumerate(players):
            scores = []
            for entry in history:
                scores.append(entry['normalized_scores'].get(player, 0))
            
            color = colors[i % len(colors)]
            
            if len(rounds) == 1:
                # Single point - show as dot with larger marker
                ax.scatter(rounds, scores, s=150, color=color, label=player, 
                          edgecolors='white', linewidth=2, zorder=5)
            else:
                # Multiple points - show as line with markers
                ax.plot(rounds, scores, marker='o', linewidth=2.5, markersize=8, 
                       label=player, color=color, markerfacecolor='white', 
                       markeredgecolor=color, markeredgewidth=2)
        
        # Customize the chart
        ax.set_title('Evolução do Desempenho - Bolão Brasileirão 2026', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Rodada', fontsize=12, fontweight='bold')
        ax.set_ylabel('Pontuação Normalizada (0-100)', fontsize=12, fontweight='bold')
        
        # Set y-axis limits
        ax.set_ylim(0, 100)
        
        # Format x-axis for rounds
        if len(rounds) == 1:
            # Single point - show with padding
            ax.set_xlim(rounds[0] - 1, rounds[0] + 1)
            ax.set_xticks([rounds[0]])
            ax.set_xticklabels([f'R{rounds[0]}'])
        else:
            # Multiple points - normal range
            ax.set_xlim(min(rounds) - 0.5, max(rounds) + 0.5)
            ax.set_xticks(rounds)
            ax.set_xticklabels([f'R{r}' for r in rounds])
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add legend
        ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True)
        
        # Highlight the latest scores
        if len(history) > 0:
            latest_entry = history[-1]
            latest_round = rounds[-1]
            for i, player in enumerate(players):
                latest_score = latest_entry['normalized_scores'].get(player, 0)
                color = colors[i % len(colors)]
                ax.annotate(f'{latest_score}', 
                           xy=(latest_round, latest_score),
                           xytext=(10, 10), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', fc=color, alpha=0.7),
                           fontweight='bold', fontsize=10, color='white')
        
        # Improve layout
        plt.tight_layout()
        
        # Save the chart
        chart_path = "performance_chart.png"
        plt.savefig(chart_path, dpi=150, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"📊 Gráfico de performance salvo em: {chart_path}")
        
        return chart_path

    def update_readme(self, actual_standings, predictions, raw_scores, force_update=False):
        """Update README.md with the latest results"""
        try:
            # Sort players by score (highest first)
            sorted_players = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
            player_names = [player[0] for player in sorted_players]

            # Calculate normalized scores for graph
            normalized_scores = {}
            for player, score in raw_scores.items():
                normalized_scores[player] = max(0, min(100, round((score - 200) / 2)))

            # Generate the results table
            results_table = []
            results_table.append("## 🏆 Resultados Atuais")
            results_table.append("")
            results_table.append(f"**Última Atualização:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            results_table.append("")

            # Create table header with players sorted by score
            header = "| Time | Real |"
            for player in player_names:
                header += f" {player} |"
            results_table.append(header)

            # Create separator
            separator = "|------|------|"
            for _ in player_names:
                separator += "------|"
            results_table.append(separator)

            # Create rows for each team
            for team_data in actual_standings:
                original_team_name = team_data['team']
                team_name = self.normalize_team_name(original_team_name)
                actual_pos = team_data['position']

                row = f"| {original_team_name} | {actual_pos} |"

                for player in player_names:
                    player_predictions = predictions[player]
                    # Find predicted position for this team
                    predicted_pos = None
                    for pos, predicted_team in player_predictions.items():
                        if predicted_team == team_name:
                            predicted_pos = int(pos)
                            break

                    if predicted_pos is not None:
                        score = self.calculate_score(predicted_pos, actual_pos)
                        row += f" {predicted_pos}°({score}p) |"
                    else:
                        row += " -- |"

                results_table.append(row)

            # Add total scores row (pontuação bruta)
            total_row = "| **TOTAL** | |"
            for player in player_names:
                total_row += f" **{raw_scores.get(player, 0)}** |"
            results_table.append(total_row)
            
            # Add ranking (pontuação normalizada)
            results_table.append("")
            results_table.append("### 🏅 Classificação Final (pontuação normalizada 0-100)")
            results_table.append("")
            for i, (player, score) in enumerate(sorted_players, 1):
                norm_score = max(0, min(100, round((score - 200) / 2)))
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                results_table.append(f"{medal} **{player}**: {norm_score} pontos")

            # Calculate current round first
            current_round = self.get_current_round(actual_standings)
            
            # Save score history and check if we need to regenerate graph
            should_update_graph = self.save_score_history(normalized_scores, raw_scores, current_round, force_update)
            
            # Generate score graph (always regenerate if scores changed or force update)
            if should_update_graph:
                print("📊 Generating updated performance chart...")
            graph_lines = self.generate_score_graph()
            results_table.extend(graph_lines)

            # Read current README
            readme_path = "README.md"
            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()

                # Find and replace the results section
                results_section = "\n".join(results_table)

                # Check if results section exists
                import re
                pattern = r'(## 🏆 Resultados Atuais.*?)(?=\n## |\Z)'
                if re.search(pattern, readme_content, flags=re.DOTALL):
                    # Replace existing results section - match everything from results until next ## or end
                    new_content = re.sub(pattern, results_section, readme_content, flags=re.DOTALL)
                else:
                    # Add results section at the beginning after the title
                    lines = readme_content.split('\n')
                    title_line = 0
                    for i, line in enumerate(lines):
                        if line.startswith('# '):
                            title_line = i
                            break
                    # Insert results after title
                    lines.insert(title_line + 1, '')
                    lines.insert(title_line + 2, results_section)
                    new_content = '\n'.join(lines)

                # Write back to README
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

                print(f"✅ Updated README.md with latest results")

            else:
                print("❌ README.md not found")

        except Exception as e:
            print(f"❌ Error updating README: {e}")
    
    def save_last_standings(self, standings, filename="last_standings.json"):
        """Save current standings to a file for comparison"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(standings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving last standings: {e}")
    
    def load_last_standings(self, filename="last_standings.json"):
        """Load last standings from file"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"❌ Error loading last standings: {e}")
        return None
    
    def standings_changed(self, current_standings, last_standings):
        """Check if standings have changed since last update"""
        if not last_standings:
            return True  # No previous data, so it's a change
        
        if len(current_standings) != len(last_standings):
            return True  # Different number of teams
        
        # Compare each team's position
        for i, current_team in enumerate(current_standings):
            if i >= len(last_standings):
                return True  # More teams than before
            
            last_team = last_standings[i]
            if (current_team['position'] != last_team['position'] or 
                current_team['team'] != last_team['team'] or
                current_team['points'] != last_team['points']):
                return True  # Position, team, or points changed
        
        return False  # No changes detected
    
    def run_comparison(self, predictions_file="bolao.json"):
        """Main method to run the comparison"""
        try:
            import sys
            force_update = False
            # Aceita 'force' como segundo argumento OU como primeiro argumento se não houver arquivo customizado
            if (len(sys.argv) > 1 and sys.argv[1].lower() == "force") or (len(sys.argv) > 2 and sys.argv[2].lower() == "force"):
                force_update = True

            # Load predictions
            predictions = self.load_predictions(predictions_file)
            team_match_map = self.build_team_match_map(self.get_teams_from_predictions(predictions))

            # Get current standings
            current_standings = self.get_current_standings(team_match_map)

            if current_standings and predictions:
                last_standings = self.load_last_standings()
                if force_update or self.standings_changed(current_standings, last_standings):
                    if force_update:
                        print("📢 Forçando atualização do README...")
                    else:
                        print("📊 Standings have changed - updating README...")
                    player_scores, raw_scores = self.compare_predictions(current_standings, predictions)
                    self.update_readme(current_standings, predictions, raw_scores, force_update)
                    self.save_last_standings(current_standings)
                    print(f"\n✅ Successfully compared {len(current_standings)} teams")
                    print(f"✅ Calculated scores for {len(predictions)} players")
                    print("✅ README updated with new standings")
                else:
                    print("📊 No changes in standings - README not updated")
                    print("🔄 Standings remain the same as last update")
                    player_scores, raw_scores = self.compare_predictions(current_standings, predictions)
                    print(f"\n✅ Successfully compared {len(current_standings)} teams")
                    print(f"✅ Calculated scores for {len(predictions)} players")
                    print("ℹ️  Use existing README for current results")
            else:
                print("❌ Failed to load data")

        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    scraper = BrasileiroScraper()
    import sys
    # Detect 'force' argument and set predictions file correctly
    args = [arg for arg in sys.argv[1:] if arg.lower() != "force"]
    predictions_file = args[0] if args else "bolao.json"
    scraper.run_comparison(predictions_file)

if __name__ == "__main__":
    main()
