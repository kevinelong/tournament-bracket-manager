from typing import List, Optional, Tuple, Dict, Callable
from dataclasses import dataclass, asdict
import math
import pygame
import sys
import json
import os
from pathlib import Path
from datetime import datetime
import uuid
import random


# Modern 2026 Color Palette
WHITE = (255, 255, 255)
BLACK = (20, 20, 30)
OFF_WHITE = (250, 250, 252)

# Grays - Higher contrast for accessibility
GRAY = (180, 184, 193)
LIGHT_GRAY = (235, 237, 242)
MED_GRAY = (140, 145, 155)
DARK_GRAY = (60, 65, 75)
CHARCOAL = (40, 44, 52)

# Primary - Modern blue with better contrast
PRIMARY = (59, 130, 246)
PRIMARY_HOVER = (96, 165, 250)
PRIMARY_LIGHT = (191, 219, 254)
PRIMARY_DARK = (29, 78, 216)

# Accent colors
ACCENT_GREEN = (16, 185, 129)
ACCENT_GREEN_HOVER = (52, 211, 153)
ACCENT_ORANGE = (251, 146, 60)
ACCENT_ORANGE_HOVER = (253, 186, 116)
ACCENT_RED = (239, 68, 68)
ACCENT_RED_HOVER = (248, 113, 113)
ACCENT_GOLD = (245, 158, 11)

# Legacy aliases for compatibility
BLUE = PRIMARY
LIGHT_BLUE = PRIMARY_LIGHT
GREEN = ACCENT_GREEN
GOLD = ACCENT_GOLD
ORANGE = ACCENT_ORANGE
RED = ACCENT_RED
BUTTON_COLOR = PRIMARY
BUTTON_HOVER = PRIMARY_HOVER

# Glassmorphism backgrounds
GLASS_BG = (255, 255, 255, 230)  # Semi-transparent white
GLASS_DARK = (40, 44, 52, 200)   # Semi-transparent dark


@dataclass
class TourStep:
    """Represents a single step in the user tour."""
    id: str
    title: str
    description: str
    tab: str  # Which tab this feature is on
    highlight_rect: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    action_required: Optional[str] = None  # What user needs to do
    validation: Optional[Callable[[], bool]] = None  # Check if step is complete


@dataclass
class TournamentMetadata:
    """Metadata for a tournament."""
    id: str
    name: str
    location: str
    date_scheduled: str  # ISO format YYYY-MM-DD
    time_scheduled: str  # HH:MM format
    date_created: str  # ISO format with time
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TournamentMetadata':
        return cls(**data)


@dataclass
class Match:
    """Represents a single match in the tournament."""
    match_id: int
    player1: Optional[str] = None
    player2: Optional[str] = None
    winner: Optional[str] = None
    round_num: int = 0
    
    def set_winner(self, winner: str):
        """Set the winner of the match."""
        if winner not in [self.player1, self.player2]:
            raise ValueError(f"{winner} is not a participant in this match")
        self.winner = winner
    
    def is_complete(self) -> bool:
        """Check if the match has been completed."""
        return self.winner is not None


class TournamentBracket:
    """Single elimination tournament bracket."""
    
    def __init__(self, participants: List[str]):
        self.participants = participants
        self.num_participants = len(participants)
        
        # Handle empty or single participant
        if self.num_participants <= 1:
            self.num_rounds = 1
            self.bracket_size = 2
        else:
            self.num_rounds = math.ceil(math.log2(self.num_participants))
            self.bracket_size = 2 ** self.num_rounds
        
        self.seeded_participants = self._seed_participants()
        self.matches: List[List[Match]] = self._initialize_matches()
    
    def _seed_participants(self) -> List[Optional[str]]:
        seeded = self.participants.copy()
        num_byes = self.bracket_size - self.num_participants
        for _ in range(num_byes):
            seeded.append(None)
        return seeded
    
    def _initialize_matches(self) -> List[List[Match]]:
        matches = []
        match_id = 0
        
        # First round
        first_round = []
        for i in range(0, self.bracket_size, 2):
            match = Match(
                match_id=match_id,
                player1=self.seeded_participants[i],
                player2=self.seeded_participants[i + 1],
                round_num=1
            )
            if match.player1 and not match.player2:
                match.winner = match.player1
            elif match.player2 and not match.player1:
                match.winner = match.player2
            
            first_round.append(match)
            match_id += 1
        
        matches.append(first_round)
        
        # Subsequent rounds
        for round_num in range(2, self.num_rounds + 1):
            round_matches = []
            num_matches = self.bracket_size // (2 ** round_num)
            
            for _ in range(num_matches):
                match = Match(match_id=match_id, round_num=round_num)
                round_matches.append(match)
                match_id += 1
            
            matches.append(round_matches)
        
        return matches
    
    def set_match_winner(self, round_num: int, match_index: int, winner: str):
        if round_num < 1 or round_num > self.num_rounds:
            raise ValueError(f"Invalid round number: {round_num}")
        
        match = self.matches[round_num - 1][match_index]
        match.set_winner(winner)
        
        if round_num < self.num_rounds:
            next_match_index = match_index // 2
            next_match = self.matches[round_num][next_match_index]
            
            if match_index % 2 == 0:
                next_match.player1 = winner
            else:
                next_match.player2 = winner
    
    def get_champion(self) -> Optional[str]:
        if self.num_rounds > 0:
            final_match = self.matches[-1][0]
            return final_match.winner
        return None
    
    def _get_round_name(self, round_num: int) -> str:
        rounds_from_end = self.num_rounds - round_num
        
        if rounds_from_end == 0:
            return "FINALS"
        elif rounds_from_end == 1:
            return "SEMI-FINALS"
        elif rounds_from_end == 2:
            return "QUARTER-FINALS"
        else:
            return f"ROUND {round_num}"
    
    def to_dict(self) -> dict:
        """Convert tournament state to dictionary for JSON serialization."""
        return {
            "participants": self.participants,
            "matches": [
                [asdict(match) for match in round_matches]
                for round_matches in self.matches
            ]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TournamentBracket':
        """Restore tournament state from dictionary."""
        bracket = cls(data["participants"])
        
        # Restore match states
        for round_idx, round_matches_data in enumerate(data["matches"]):
            for match_idx, match_data in enumerate(round_matches_data):
                match = bracket.matches[round_idx][match_idx]
                match.player1 = match_data["player1"]
                match.player2 = match_data["player2"]
                match.winner = match_data["winner"]
        
        return bracket


class TournamentBracketGUI:
    """Interactive pygame GUI for tournament brackets."""
    
    def __init__(self, width: int = 1400, height: int = 800):
        pygame.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Tournament Manager")
        
        # Tab system
        self.tabs = ["Tournaments", "Current Tournament", "Player List", "Bracket", "Final Results"]
        self.active_tab = "Tournaments"
        self.tab_height = 50
        
        # Multi-tournament system
        self.tournaments_dir = Path("tournaments")
        self.tournaments_dir.mkdir(exist_ok=True)
        self.current_tournament_id: Optional[str] = None
        self.current_metadata: Optional[TournamentMetadata] = None
        
        # Initialize with empty tournament
        self.bracket: Optional[TournamentBracket] = None
        self.initial_participants: List[str] = []
        self.editing_players: List[str] = []
        
        # Recalculate scaling
        self._recalculate_scaling()
        
        self.selected_match: Optional[Tuple[int, int]] = None
        self.hovered_player: Optional[Tuple[int, int, int]] = None
        
        self.scroll_offset = 0
        self.show_instructions = True
        
        # UI state
        self.dangerous_panel_open = False
        self.show_close_confirm = False
        self.hovered_close_button = False
        
        # Text editing state
        self.active_input_field: Optional[str] = None  # Which field is being edited
        self.input_text = ""  # Current text being edited
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # Player list editing
        self.new_player_name = ""
        self.editing_player_index: Optional[int] = None
        
        # Tour system
        self.tour_active = False
        self.tour_step_index = 0
        self.tour_steps: List[TourStep] = []
        self._initialize_tour_steps()
        
        # Buttons
        self.close_button_rect = pygame.Rect(self.width - 50, 10, 30, 30)
        
        self.clock = pygame.time.Clock()
        
        # Load tournament list
        self.load_tournaments_list()
    
    def _recalculate_scaling(self):
        """Recalculate UI scaling based on current participant count."""
        self.num_participants = len(self.editing_players)
        self.num_rounds = self.bracket.num_rounds if self.bracket else 1
        
        # Scale fonts based on participant count - larger for better readability
        if self.num_participants <= 8:
            title_size, round_size, player_size, small_size, button_size = 52, 34, 26, 22, 30
            self.match_width, self.match_height = 220, 90
        elif self.num_participants <= 16:
            title_size, round_size, player_size, small_size, button_size = 46, 30, 22, 20, 26
            self.match_width, self.match_height = 200, 80
        elif self.num_participants <= 32:
            title_size, round_size, player_size, small_size, button_size = 40, 26, 20, 18, 24
            self.match_width, self.match_height = 180, 70
        else:
            title_size, round_size, player_size, small_size, button_size = 36, 22, 18, 16, 22
            self.match_width, self.match_height = 160, 60
        
        self.title_font = pygame.font.Font(None, title_size)
        self.round_font = pygame.font.Font(None, round_size)
        self.player_font = pygame.font.Font(None, player_size)
        self.small_font = pygame.font.Font(None, small_size)
        self.button_font = pygame.font.Font(None, button_size)
        
        self.player_height = self.match_height // 2 - 5
    
    def _draw_card(self, rect: pygame.Rect, color=None, border_color=None, shadow=True, glow=False):
        """Draw a modern card with glassmorphism effect."""
        if color is None:
            color = OFF_WHITE
        if border_color is None:
            border_color = MED_GRAY
        
        # Shadow for depth
        if shadow:
            shadow_surf = pygame.Surface((rect.width + 4, rect.height + 4), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, 20), shadow_surf.get_rect(), border_radius=12)
            self.screen.blit(shadow_surf, (rect.x + 2, rect.y + 4))
        
        # Glow effect (for hover states)
        if glow and border_color:
            glow_surf = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*border_color, 50), glow_surf.get_rect(), border_radius=14)
            self.screen.blit(glow_surf, (rect.x - 6, rect.y - 6))
        
        # Main card
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=10)
    
    def _draw_button(self, rect: pygame.Rect, text: str, color=None, hover=False, disabled=False):
        """Draw a modern button with micro-interactions."""
        if disabled:
            bg_color = MED_GRAY
            text_color = DARK_GRAY
        elif color:
            bg_color = color
            text_color = WHITE
        else:
            bg_color = PRIMARY_HOVER if hover else PRIMARY
            text_color = WHITE
        
        # Hover effect - slightly larger
        draw_rect = rect.copy()
        if hover and not disabled:
            draw_rect.inflate_ip(4, 2)
            # Glow
            glow = pygame.Surface((draw_rect.width + 8, draw_rect.height + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*bg_color, 60), glow.get_rect(), border_radius=10)
            self.screen.blit(glow, (draw_rect.x - 4, draw_rect.y - 4))
        
        # Shadow
        if not disabled:
            shadow = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 30), shadow.get_rect(), border_radius=8)
            self.screen.blit(shadow, (draw_rect.x + 2, draw_rect.y + 3))
        
        # Button
        pygame.draw.rect(self.screen, bg_color, draw_rect, border_radius=8)
        
        # Text
        text_surf = self.button_font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        self.screen.blit(text_surf, text_rect)
    
    def _get_match_spacing(self, num_matches: int) -> float:
        """Calculate match spacing ensuring no overlap."""
        available_height = self.height - self.tab_height - 120 - 150
        min_spacing_needed = self.match_height + 10
        total_height_needed = num_matches * min_spacing_needed
        
        if total_height_needed > available_height:
            return min_spacing_needed
        else:
            return available_height / max(num_matches, 1)
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_current_tournament()
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # Check tour overlay clicks first
                        if self._handle_tour_click(event.pos):
                            continue
                        # Check tab clicks
                        if self._handle_tab_click(event.pos):
                            continue
                        self._handle_click(event.pos)
                        
                        # Check if trying to close
                        if running == False:
                            break
                    elif event.button == 4:
                        self.scroll_offset = min(0, self.scroll_offset + 30)
                    elif event.button == 5:
                        self.scroll_offset -= 30
                elif event.type == pygame.MOUSEMOTION:
                    self._handle_hover(event.pos)
                elif event.type == pygame.KEYDOWN:
                    # Handle text input for editable fields on Current Tournament tab
                    if self.active_tab == "Current Tournament" and self.active_input_field:
                        if event.key == pygame.K_BACKSPACE:
                            self.input_text = self.input_text[:-1]
                        elif event.key == pygame.K_RETURN:
                            # Save the edited value
                            if self.active_input_field == "tournament_name":
                                self.current_metadata.name = self.input_text
                            elif self.active_input_field == "tournament_location":
                                self.current_metadata.location = self.input_text
                            elif self.active_input_field == "tournament_date":
                                self.current_metadata.date_scheduled = self.input_text
                            elif self.active_input_field == "tournament_time":
                                self.current_metadata.time_scheduled = self.input_text
                            
                            self.active_input_field = None
                            self.input_text = ""
                            self.save_current_tournament()
                        elif event.key == pygame.K_ESCAPE:
                            # Cancel editing
                            self.active_input_field = None
                            self.input_text = ""
                        elif event.unicode.isprintable() and len(self.input_text) < 50:
                            self.input_text += event.unicode
                    # Handle text input for player names on Player List tab
                    elif self.active_tab == "Player List":
                        if event.key == pygame.K_BACKSPACE:
                            self.new_player_name = self.new_player_name[:-1]
                        elif event.key == pygame.K_RETURN and self.new_player_name.strip():
                            self.editing_players.append(self.new_player_name.strip())
                            self.new_player_name = ""
                            self._recalculate_scaling()
                            self.save_current_tournament()
                        elif event.unicode.isprintable() and len(self.new_player_name) < 30:
                            self.new_player_name += event.unicode
                    else:
                        if event.key == pygame.K_ESCAPE:
                            if self.tour_active:
                                self.end_tour()
                            elif self.show_close_confirm:
                                self.show_close_confirm = False
                            else:
                                self.selected_match = None
                        elif event.key == pygame.K_t:
                            # Start/restart tour
                            self.start_tour()
                        elif event.key == pygame.K_h:
                            self.show_instructions = not self.show_instructions
            
            # Update cursor blink animation (every 30 frames = 0.5 seconds at 60 FPS)
            self.cursor_timer += 1
            if self.cursor_timer >= 30:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
            
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def _draw(self):
        # Modern gradient background
        for y in range(self.height):
            ratio = y / self.height
            r = int(LIGHT_GRAY[0] * (1 - ratio * 0.05) + OFF_WHITE[0] * (ratio * 0.05))
            g = int(LIGHT_GRAY[1] * (1 - ratio * 0.05) + OFF_WHITE[1] * (ratio * 0.05))
            b = int(LIGHT_GRAY[2] * (1 - ratio * 0.05) + OFF_WHITE[2] * (ratio * 0.05))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))
        
        # Draw tabs
        self._draw_tabs()
        
        # Draw content based on active tab
        if self.active_tab == "Tournaments":
            self._draw_tournaments_list_tab()
        elif self.active_tab == "Current Tournament":
            self._draw_current_tournament_tab()
        elif self.active_tab == "Player List":
            self._draw_player_list_tab()
        elif self.active_tab == "Bracket":
            self._draw_bracket_tab()
        elif self.active_tab == "Final Results":
            self._draw_final_results_tab()
        
        # Draw close confirmation dialog (on top of everything)
        if self.show_close_confirm:
            self._draw_close_confirmation()
        
        # Draw tour overlay (on top of everything else)
        if self.tour_active:
            self._draw_tour_overlay()
    
    def _draw_tabs(self):
        """Draw the tab navigation bar."""
        tab_width = self.width / len(self.tabs)
        
        for i, tab_name in enumerate(self.tabs):
            x = i * tab_width
            tab_rect = pygame.Rect(x, 0, tab_width, self.tab_height)
            
            # Draw tab background with modern style
            if tab_name == self.active_tab:
                # Active tab - elevated card style
                color = OFF_WHITE
                border_color = PRIMARY
                border_width = 3
                
                # Subtle shadow for depth
                shadow = pygame.Surface((tab_width, self.tab_height), pygame.SRCALPHA)
                shadow.fill((0, 0, 0, 15))
                self.screen.blit(shadow, (x + 2, 2))
            else:
                # Inactive tab - subtle style
                color = LIGHT_GRAY
                border_color = MED_GRAY
                border_width = 0
            
            pygame.draw.rect(self.screen, color, tab_rect, border_radius=8)
            if border_width > 0:
                pygame.draw.rect(self.screen, border_color, tab_rect, border_width, border_radius=8)
            
            # Draw tab text with better color
            text_color = CHARCOAL if tab_name == self.active_tab else DARK_GRAY
            text_surface = self.round_font.render(tab_name, True, text_color)
            text_rect = text_surface.get_rect(center=(x + tab_width / 2, self.tab_height / 2))
            self.screen.blit(text_surface, text_rect)
        
        # Draw close button in top right with modern style
        close_color = ACCENT_RED if self.hovered_close_button else CHARCOAL
        pygame.draw.rect(self.screen, close_color, self.close_button_rect, border_radius=6)
        
        # Add subtle glow on hover
        if self.hovered_close_button:
            glow = pygame.Surface((self.close_button_rect.width + 8, self.close_button_rect.height + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*ACCENT_RED, 40), glow.get_rect(), border_radius=8)
            self.screen.blit(glow, (self.close_button_rect.x - 4, self.close_button_rect.y - 4))
        
        # Draw X
        x_offset = 10
        y_offset = 10
        pygame.draw.line(self.screen, WHITE, 
                        (self.close_button_rect.x + x_offset, self.close_button_rect.y + y_offset),
                        (self.close_button_rect.x + self.close_button_rect.width - x_offset, 
                         self.close_button_rect.y + self.close_button_rect.height - y_offset), 3)
        pygame.draw.line(self.screen, WHITE,
                        (self.close_button_rect.x + self.close_button_rect.width - x_offset, 
                         self.close_button_rect.y + y_offset),
                        (self.close_button_rect.x + x_offset, 
                         self.close_button_rect.y + self.close_button_rect.height - y_offset), 3)
    
    def _handle_tab_click(self, pos) -> bool:
        """Handle clicks on tabs. Returns True if a tab was clicked."""
        mx, my = pos
        if my <= self.tab_height:
            tab_width = self.width / len(self.tabs)
            tab_index = int(mx / tab_width)
            if 0 <= tab_index < len(self.tabs):
                self.active_tab = self.tabs[tab_index]
                self.selected_match = None  # Clear selection when switching tabs
                return True
        return False
    
    def _draw_bracket_tab(self):
        """Draw the bracket view (existing functionality)."""
        if not self.bracket:
            # No bracket generated yet
            y_offset = self.height // 2 - 50
            msg = self.round_font.render("No bracket generated yet", True, DARK_GRAY)
            msg_rect = msg.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(msg, msg_rect)
            
            msg2 = self.small_font.render("Add players in 'Player List' tab and click 'Generate Bracket'", True, DARK_GRAY)
            msg2_rect = msg2.get_rect(center=(self.width // 2, y_offset + 40))
            self.screen.blit(msg2, msg2_rect)
            return
        
        champion = self.bracket.get_champion()
        if champion:
            title_text = f"CHAMPION: {champion}"
            title_color = GOLD
        else:
            title_text = "Tournament Bracket"
            title_color = BLACK
        
        title_surface = self.title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(self.width // 2, self.tab_height + 40))
        self.screen.blit(title_surface, title_rect)
        
        self._draw_rounds()
        self._draw_connections()
        
        if self.show_instructions:
            self._draw_instructions()
        
        if self.selected_match:
            self._draw_selection_prompt()
    
    def _draw_tournaments_list_tab(self):
        """Draw the tournaments list (all saved tournaments)."""
        y_offset = self.tab_height + 80
        
        # Title
        title = self.title_font.render("Tournaments", True, BLUE)
        title_rect = title.get_rect(center=(self.width // 2, y_offset))
        self.screen.blit(title, title_rect)
        
        y_offset += 80
        
        if not self.tournaments_list:
            # No tournaments message
            no_tournaments = self.round_font.render("No tournaments yet. Click 'Create New' to start!", True, DARK_GRAY)
            no_tournaments_rect = no_tournaments.get_rect(center=(self.width // 2, y_offset + 100))
            self.screen.blit(no_tournaments, no_tournaments_rect)
        else:
            # List tournaments
            for i, tournament in enumerate(self.tournaments_list):
                tournament_rect = pygame.Rect(100, y_offset, self.width - 200, 70)
                
                # Background
                bg_color = WHITE if i % 2 == 0 else LIGHT_GRAY
                pygame.draw.rect(self.screen, bg_color, tournament_rect, border_radius=5)
                pygame.draw.rect(self.screen, BLUE, tournament_rect, 2, border_radius=5)
                
                # Tournament name
                name_text = self.round_font.render(tournament.name, True, BLACK)
                self.screen.blit(name_text, (120, y_offset + 10))
                
                # Location and date
                info_text = self.small_font.render(
                    f"📍 {tournament.location} | 📅 {tournament.date_scheduled} {tournament.time_scheduled}",
                    True, DARK_GRAY
                )
                self.screen.blit(info_text, (120, y_offset + 40))
                
                y_offset += 80
        
        # Create new button
        create_button_rect = pygame.Rect(self.width // 2 - 120, self.height - 80, 240, 50)
        pygame.draw.rect(self.screen, GREEN, create_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, DARK_GRAY, create_button_rect, 2, border_radius=5)
        create_text = self.button_font.render("Create New Tournament", True, WHITE)
        create_text_rect = create_text.get_rect(center=create_button_rect.center)
        self.screen.blit(create_text, create_text_rect)
    
    def _draw_current_tournament_tab(self):
        """Draw tournament setup and configuration."""
        if not self.current_metadata:
            # No tournament selected
            y_offset = self.height // 2 - 50
            msg = self.round_font.render("No tournament selected", True, DARK_GRAY)
            msg_rect = msg.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(msg, msg_rect)
            
            msg2 = self.small_font.render("Go to 'Tournaments' tab to create or load a tournament", True, DARK_GRAY)
            msg2_rect = msg2.get_rect(center=(self.width // 2, y_offset + 40))
            self.screen.blit(msg2, msg2_rect)
            return
        
        y_offset = self.tab_height + 80
        
        # Title
        title = self.title_font.render("Current Tournament", True, BLUE)
        title_rect = title.get_rect(center=(self.width // 2, y_offset))
        self.screen.blit(title, title_rect)
        
        y_offset += 80
        
        # Tournament name - EDITABLE
        name_label = self.round_font.render("Name:", True, CHARCOAL)
        self.screen.blit(name_label, (100, y_offset))
        
        name_rect = pygame.Rect(300, y_offset - 8, 500, 40)
        is_editing_name = self.active_input_field == "tournament_name"
        
        # Draw input box with clear "editable" styling
        if is_editing_name:
            self._draw_card(name_rect, OFF_WHITE, PRIMARY, shadow=True, glow=True)
            display_text = self.input_text + ("|" if self.cursor_visible else "")
        else:
            self._draw_card(name_rect, LIGHT_GRAY, MED_GRAY, shadow=False)
            display_text = self.current_metadata.name
            # Add edit icon hint
            edit_hint = self.small_font.render("✎ click to edit", True, MED_GRAY)
            self.screen.blit(edit_hint, (name_rect.right + 10, name_rect.centery - 8))
        
        name_text = self.player_font.render(display_text, True, CHARCOAL)
        self.screen.blit(name_text, (name_rect.x + 12, name_rect.y + 10))
        y_offset += 60
        
        # Location - EDITABLE
        location_label = self.round_font.render("Location:", True, CHARCOAL)
        self.screen.blit(location_label, (100, y_offset))
        
        location_rect = pygame.Rect(300, y_offset - 8, 500, 40)
        is_editing_location = self.active_input_field == "tournament_location"
        
        if is_editing_location:
            self._draw_card(location_rect, OFF_WHITE, PRIMARY, shadow=True, glow=True)
            display_text = self.input_text + ("|" if self.cursor_visible else "")
        else:
            self._draw_card(location_rect, LIGHT_GRAY, MED_GRAY, shadow=False)
            display_text = self.current_metadata.location
            edit_hint = self.small_font.render("✎ click to edit", True, MED_GRAY)
            self.screen.blit(edit_hint, (location_rect.right + 10, location_rect.centery - 8))
        
        location_text = self.player_font.render(display_text, True, CHARCOAL)
        self.screen.blit(location_text, (location_rect.x + 12, location_rect.y + 10))
        y_offset += 60
        
        # Date scheduled - EDITABLE
        date_label = self.round_font.render("Date:", True, CHARCOAL)
        self.screen.blit(date_label, (100, y_offset))
        
        date_rect = pygame.Rect(300, y_offset - 8, 250, 40)
        is_editing_date = self.active_input_field == "tournament_date"
        
        if is_editing_date:
            self._draw_card(date_rect, OFF_WHITE, PRIMARY, shadow=True, glow=True)
            display_text = self.input_text + ("|" if self.cursor_visible else "")
        else:
            self._draw_card(date_rect, LIGHT_GRAY, MED_GRAY, shadow=False)
            display_text = self.current_metadata.date_scheduled
            edit_hint = self.small_font.render("✎", True, MED_GRAY)
            self.screen.blit(edit_hint, (date_rect.right + 10, date_rect.centery - 8))
        
        date_text = self.player_font.render(display_text, True, CHARCOAL)
        self.screen.blit(date_text, (date_rect.x + 12, date_rect.y + 10))
        
        # Time scheduled - EDITABLE
        time_rect = pygame.Rect(570, y_offset - 8, 230, 40)
        is_editing_time = self.active_input_field == "tournament_time"
        
        if is_editing_time:
            self._draw_card(time_rect, OFF_WHITE, PRIMARY, shadow=True, glow=True)
            display_text = self.input_text + ("|" if self.cursor_visible else "")
        else:
            self._draw_card(time_rect, LIGHT_GRAY, MED_GRAY, shadow=False)
            display_text = self.current_metadata.time_scheduled
            edit_hint = self.small_font.render("✎", True, MED_GRAY)
            self.screen.blit(edit_hint, (time_rect.right + 10, time_rect.centery - 8))
        
        time_text = self.player_font.render(display_text, True, CHARCOAL)
        self.screen.blit(time_text, (time_rect.x + 12, time_rect.y + 10))
        y_offset += 60
        
        # Date created
        created_label = self.round_font.render("Created:", True, BLACK)
        self.screen.blit(created_label, (100, y_offset))
        created_date = self.current_metadata.date_created.split('T')[0]  # Get date part
        created_text = self.player_font.render(created_date, True, DARK_GRAY)
        self.screen.blit(created_text, (300, y_offset))
        y_offset += 60
        
        # Number of participants
        participants_label = self.round_font.render("Participants:", True, BLACK)
        self.screen.blit(participants_label, (100, y_offset))
        participant_text = self.player_font.render(f"{len(self.editing_players)} players", True, DARK_GRAY)
        self.screen.blit(participant_text, (300, y_offset))
        y_offset += 50
        
        # Tournament format
        format_label = self.round_font.render("Format:", True, BLACK)
        self.screen.blit(format_label, (100, y_offset))
        format_text = self.player_font.render("Single Elimination", True, DARK_GRAY)
        self.screen.blit(format_text, (300, y_offset))
        y_offset += 50
        
        # Rounds (if bracket exists)
        if self.bracket:
            rounds_label = self.round_font.render("Rounds:", True, BLACK)
            self.screen.blit(rounds_label, (100, y_offset))
            rounds_text = self.player_font.render(f"{self.num_rounds} rounds", True, DARK_GRAY)
            self.screen.blit(rounds_text, (300, y_offset))
            y_offset += 60
        
        # Status
        if self.bracket and self.bracket.get_champion():
            status_text = self.round_font.render("Status: COMPLETED", True, GOLD)
        elif self.bracket:
            status_text = self.round_font.render("Status: IN PROGRESS", True, GREEN)
        else:
            status_text = self.round_font.render("Status: NOT STARTED", True, ORANGE)
        
        status_rect = status_text.get_rect(center=(self.width // 2, y_offset))
        self.screen.blit(status_text, status_rect)
        
        y_offset += 60
        
        # Instructions
        instructions = [
            "Switch to 'Player List' to view all participants",
            "Switch to 'Bracket' to view and interact with the tournament",
            "Switch to 'Final Results' to see tournament statistics"
        ]
        
        for instruction in instructions:
            inst_text = self.small_font.render(instruction, True, DARK_GRAY)
            inst_rect = inst_text.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(inst_text, inst_rect)
            y_offset += 30
        
        # Dangerous Operations Panel
        panel_y = self.tab_height + 450
        panel_rect = pygame.Rect(100, panel_y, self.width - 200, 40)
        
        # Draw panel header (always visible)
        panel_color = ORANGE if self.dangerous_panel_open else RED
        pygame.draw.rect(self.screen, panel_color, panel_rect, border_radius=5)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect, 2, border_radius=5)
        
        # Draw warning icon and text
        warning_text = "⚠ DANGEROUS OPERATIONS"
        arrow = "▼" if self.dangerous_panel_open else "▶"
        panel_label = self.round_font.render(f"{arrow} {warning_text}", True, WHITE)
        panel_label_rect = panel_label.get_rect(center=(self.width // 2, panel_y + 20))
        self.screen.blit(panel_label, panel_label_rect)
        
        # Draw panel content if open
        if self.dangerous_panel_open:
            content_rect = pygame.Rect(100, panel_y + 50, self.width - 200, 140)
            pygame.draw.rect(self.screen, LIGHT_GRAY, content_rect, border_radius=5)
            pygame.draw.rect(self.screen, RED, content_rect, 2, border_radius=5)
            
            # Warning message
            warning_msg = self.small_font.render("These operations cannot be undone!", True, RED)
            warning_rect = warning_msg.get_rect(center=(self.width // 2, panel_y + 80))
            self.screen.blit(warning_msg, warning_rect)
            
            # Reset button
            reset_btn_rect = pygame.Rect(self.width // 2 - 220, panel_y + 120, 200, 50)
            pygame.draw.rect(self.screen, RED, reset_btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, DARK_GRAY, reset_btn_rect, 2, border_radius=5)
            reset_text = self.button_font.render("Reset Tournament", True, WHITE)
            reset_text_rect = reset_text.get_rect(center=reset_btn_rect.center)
            self.screen.blit(reset_text, reset_text_rect)
            
            # Reshuffle button
            reshuffle_btn_rect = pygame.Rect(self.width // 2 + 20, panel_y + 120, 200, 50)
            pygame.draw.rect(self.screen, ORANGE, reshuffle_btn_rect, border_radius=5)
            pygame.draw.rect(self.screen, DARK_GRAY, reshuffle_btn_rect, 2, border_radius=5)
            reshuffle_text = self.button_font.render("Reshuffle Players", True, WHITE)
            reshuffle_text_rect = reshuffle_text.get_rect(center=reshuffle_btn_rect.center)
            self.screen.blit(reshuffle_text, reshuffle_text_rect)
    
    def _draw_player_list_tab(self):
        """Draw the editable player list."""
        if not self.current_metadata:
            # No tournament selected
            y_offset = self.height // 2 - 50
            msg = self.round_font.render("No tournament selected", True, DARK_GRAY)
            msg_rect = msg.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(msg, msg_rect)
            return
        
        y_offset = self.tab_height + 80
        
        # Title
        title = self.title_font.render("Player List", True, BLUE)
        title_rect = title.get_rect(center=(self.width // 2, y_offset))
        self.screen.blit(title, title_rect)
        
        y_offset += 60
        
        # Subtitle
        subtitle = self.round_font.render(f"Total Participants: {len(self.editing_players)}", True, DARK_GRAY)
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, y_offset))
        self.screen.blit(subtitle, subtitle_rect)
        
        y_offset += 60
        
        # Input field for new player
        input_label = self.small_font.render("Add New Player:", True, BLACK)
        self.screen.blit(input_label, (self.width // 2 - 200, y_offset))
        
        input_box = pygame.Rect(self.width // 2 - 200, y_offset + 25, 400, 35)
        pygame.draw.rect(self.screen, WHITE, input_box, border_radius=5)
        pygame.draw.rect(self.screen, BLUE, input_box, 2, border_radius=5)
        
        input_text = self.player_font.render(self.new_player_name + "|", True, BLACK)
        self.screen.blit(input_text, (input_box.x + 10, input_box.y + 8))
        
        y_offset += 80
        
        # Player list
        if not self.editing_players:
            no_players = self.small_font.render("No players yet. Add players above and press Enter or click 'Add Player'", True, DARK_GRAY)
            no_players_rect = no_players.get_rect(center=(self.width // 2, y_offset + 50))
            self.screen.blit(no_players, no_players_rect)
        else:
            for i, player in enumerate(self.editing_players):
                y = y_offset + i * 35
                
                # Player box
                player_box = pygame.Rect(self.width // 2 - 200, y, 360, 30)
                pygame.draw.rect(self.screen, WHITE, player_box, border_radius=3)
                pygame.draw.rect(self.screen, BLUE, player_box, 1, border_radius=3)
                
                # Player name
                player_text = self.small_font.render(f"{i+1}. {player}", True, BLACK)
                self.screen.blit(player_text, (player_box.x + 10, y + 6))
                
                # Remove button (X)
                remove_btn = pygame.Rect(self.width // 2 + 180, y, 30, 30)
                pygame.draw.rect(self.screen, RED, remove_btn, border_radius=3)
                remove_text = self.small_font.render("✕", True, WHITE)
                remove_text_rect = remove_text.get_rect(center=remove_btn.center)
                self.screen.blit(remove_text, remove_text_rect)
        
        # Add player button
        add_button_rect = pygame.Rect(self.width // 2 - 100, self.height - 120, 200, 50)
        add_button_color = GREEN if self.new_player_name.strip() else GRAY
        pygame.draw.rect(self.screen, add_button_color, add_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, DARK_GRAY, add_button_rect, 2, border_radius=5)
        add_text = self.button_font.render("Add Player", True, WHITE)
        add_text_rect = add_text.get_rect(center=add_button_rect.center)
        self.screen.blit(add_text, add_text_rect)
        
        # Generate bracket button
        generate_button_rect = pygame.Rect(self.width // 2 - 120, self.height - 60, 240, 50)
        generate_button_color = BLUE if len(self.editing_players) >= 2 else GRAY
        pygame.draw.rect(self.screen, generate_button_color, generate_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, DARK_GRAY, generate_button_rect, 2, border_radius=5)
        generate_text = self.button_font.render("Generate Bracket", True, WHITE)
        generate_text_rect = generate_text.get_rect(center=generate_button_rect.center)
        self.screen.blit(generate_text, generate_text_rect)
    
    def _draw_final_results_tab(self):
        """Draw final results and statistics."""
        if not self.bracket:
            # No bracket yet
            y_offset = self.height // 2 - 50
            msg = self.round_font.render("No tournament results yet", True, DARK_GRAY)
            msg_rect = msg.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(msg, msg_rect)
            return
        
        y_offset = self.tab_height + 80
        
        # Title
        title = self.title_font.render("Final Results", True, BLUE)
        title_rect = title.get_rect(center=(self.width // 2, y_offset))
        self.screen.blit(title, title_rect)
        
        y_offset += 80
        
        # Check if tournament is complete
        champion = self.bracket.get_champion()
        
        if champion:
            # Champion display
            champion_label = self.round_font.render("CHAMPION", True, GOLD)
            champion_rect = champion_label.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(champion_label, champion_rect)
            
            y_offset += 50
            
            # Draw trophy icon (simple)
            trophy_size = 80
            trophy_rect = pygame.Rect(self.width // 2 - trophy_size // 2, y_offset, trophy_size, trophy_size)
            pygame.draw.circle(self.screen, GOLD, (self.width // 2, y_offset + 25), 30)
            pygame.draw.rect(self.screen, GOLD, pygame.Rect(self.width // 2 - 15, y_offset + 40, 30, 35))
            
            y_offset += 90
            
            champion_name = self.title_font.render(champion, True, GOLD)
            champion_name_rect = champion_name.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(champion_name, champion_name_rect)
            
            y_offset += 80
            
            # Get finalists from final match
            final_match = self.bracket.matches[-1][0]
            runner_up = final_match.player1 if final_match.player2 == champion else final_match.player2
            
            if runner_up:
                runner_label = self.round_font.render("Runner-Up (2nd Place)", True, DARK_GRAY)
                runner_rect = runner_label.get_rect(center=(self.width // 2, y_offset))
                self.screen.blit(runner_label, runner_rect)
                
                y_offset += 40
                
                runner_name = self.player_font.render(runner_up, True, BLACK)
                runner_name_rect = runner_name.get_rect(center=(self.width // 2, y_offset))
                self.screen.blit(runner_name, runner_name_rect)
                
                y_offset += 70
            
            # Get semi-finalists if semifinals exist
            if len(self.bracket.matches) > 1:
                semi_matches = self.bracket.matches[-2]
                semi_finalists = []
                for match in semi_matches:
                    if match.player1 and match.player1 != champion and match.player1 != runner_up:
                        semi_finalists.append(match.player1)
                    if match.player2 and match.player2 != champion and match.player2 != runner_up:
                        semi_finalists.append(match.player2)
                
                if semi_finalists:
                    semi_label = self.round_font.render("Semi-Finalists (3rd/4th Place)", True, DARK_GRAY)
                    semi_rect = semi_label.get_rect(center=(self.width // 2, y_offset))
                    self.screen.blit(semi_label, semi_rect)
                    
                    y_offset += 40
                    
                    for sf in semi_finalists[:2]:  # Max 2 semi-finalists
                        sf_name = self.player_font.render(sf, True, BLACK)
                        sf_rect = sf_name.get_rect(center=(self.width // 2, y_offset))
                        self.screen.blit(sf_name, sf_rect)
                        y_offset += 35
            
            y_offset += 40
            
            # Tournament stats
            stats_label = self.round_font.render("Tournament Statistics", True, BLUE)
            stats_rect = stats_label.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(stats_label, stats_rect)
            
            y_offset += 50
            
            total_matches = sum(len(round_matches) for round_matches in self.bracket.matches)
            completed_matches = sum(1 for round_matches in self.bracket.matches for match in round_matches if match.winner)
            
            stats = [
                f"Total Matches: {total_matches}",
                f"Completed Matches: {completed_matches}",
                f"Rounds Played: {self.num_rounds}",
                f"Participants: {self.num_participants}"
            ]
            
            for stat in stats:
                stat_text = self.small_font.render(stat, True, BLACK)
                stat_rect = stat_text.get_rect(center=(self.width // 2, y_offset))
                self.screen.blit(stat_text, stat_rect)
                y_offset += 30
        else:
            # Tournament not complete
            not_complete = self.round_font.render("Tournament Not Yet Complete", True, ORANGE)
            not_complete_rect = not_complete.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(not_complete, not_complete_rect)
            
            y_offset += 80
            
            total_matches = sum(len(round_matches) for round_matches in self.bracket.matches)
            completed_matches = sum(1 for round_matches in self.bracket.matches for match in round_matches if match.winner)
            
            progress_text = self.player_font.render(
                f"Progress: {completed_matches} of {total_matches} matches completed",
                True, DARK_GRAY
            )
            progress_rect = progress_text.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(progress_text, progress_rect)
            
            y_offset += 60
            
            instruction = self.small_font.render(
                "Switch to 'Bracket' tab to continue the tournament",
                True, DARK_GRAY
            )
            instruction_rect = instruction.get_rect(center=(self.width // 2, y_offset))
            self.screen.blit(instruction, instruction_rect)
        
        champion = self.bracket.get_champion()
        if champion:
            title_text = f"CHAMPION: {champion}"
            title_color = GOLD
        else:
            title_text = "Tournament Bracket"
            title_color = BLACK
        
        title_surface = self.title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(center=(self.width // 2, 40))
        self.screen.blit(title_surface, title_rect)
        
        self._draw_rounds()
        self._draw_connections()
        
        if self.show_instructions:
            self._draw_instructions()
        
        if self.selected_match:
            self._draw_selection_prompt()
    
    def _draw_rounds(self):
        num_rounds = self.bracket.num_rounds
        round_spacing = (self.width - 100) / num_rounds
        start_y = self.tab_height + 120  # Offset for tab bar
        
        for round_num, round_matches in enumerate(self.bracket.matches, 1):
            x = 50 + round_num * round_spacing - round_spacing / 2
            
            round_name = self.bracket._get_round_name(round_num)
            round_surface = self.round_font.render(round_name, True, BLUE)
            round_rect = round_surface.get_rect(center=(x, start_y))
            self.screen.blit(round_surface, round_rect)
            
            num_matches = len(round_matches)
            match_spacing = self._get_match_spacing(num_matches)
            
            for idx, match in enumerate(round_matches):
                y = start_y + 50 + idx * match_spacing + self.scroll_offset
                
                if -self.match_height < y < self.height:
                    self._draw_match(match, x, y, round_num, idx)
    
    def _draw_match(self, match: Match, x: float, y: float, round_num: int, match_idx: int):
        is_selected = self.selected_match == (round_num, match_idx)
        
        box_rect = pygame.Rect(
            x - self.match_width // 2,
            y,
            self.match_width,
            self.match_height
        )
        
        # Modern shadow with blur simulation
        for i in range(3):
            shadow_rect = box_rect.copy()
            shadow_rect.x += 2 + i
            shadow_rect.y += 3 + i
            alpha = 15 - i * 5
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(shadow_surf, (0, 0, 0, alpha), shadow_surf.get_rect(), border_radius=10)
            self.screen.blit(shadow_surf, shadow_rect)
        
        # Card background
        border_color = ACCENT_ORANGE if is_selected else PRIMARY
        border_width = 3 if is_selected else 2
        
        # Glassmorphic effect
        pygame.draw.rect(self.screen, OFF_WHITE, box_rect, border_radius=10)
        
        # Glow on selection
        if is_selected:
            glow = pygame.Surface((box_rect.width + 12, box_rect.height + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*ACCENT_ORANGE, 40), glow.get_rect(), border_radius=12)
            self.screen.blit(glow, (box_rect.x - 6, box_rect.y - 6))
        
        pygame.draw.rect(self.screen, border_color, box_rect, border_width, border_radius=10)
        
        player1_rect = pygame.Rect(box_rect.x, box_rect.y, box_rect.width, self.player_height)
        player2_rect = pygame.Rect(box_rect.x, box_rect.y + self.player_height, box_rect.width, self.player_height)
        
        self._draw_player(match, player1_rect, match.player1, 1, round_num, match_idx)
        
        # Divider line with subtle gradient
        pygame.draw.line(
            self.screen,
            MED_GRAY,
            (box_rect.x + 5, box_rect.y + self.player_height),
            (box_rect.x + box_rect.width - 5, box_rect.y + self.player_height),
            1
        )
        
        self._draw_player(match, player2_rect, match.player2, 2, round_num, match_idx)
        
        # Match number badge
        badge_rect = pygame.Rect(box_rect.x + 5, box_rect.y + box_rect.height - 22, 35, 18)
        pygame.draw.rect(self.screen, PRIMARY_LIGHT, badge_rect, border_radius=4)
        match_num_surface = self.small_font.render(f"M{match.match_id + 1}", True, PRIMARY_DARK)
        text_rect = match_num_surface.get_rect(center=badge_rect.center)
        self.screen.blit(match_num_surface, text_rect)
    
    def _draw_player(self, match: Match, rect: pygame.Rect, player: Optional[str], 
                     player_num: int, round_num: int, match_idx: int):
        is_hovered = self.hovered_player == (round_num, match_idx, player_num)
        is_winner = player and match.winner == player
        is_loser = player and match.winner and match.winner != player
        
        # Modern status colors
        if is_winner:
            bg_color = ACCENT_GREEN
            text_color = WHITE
        elif is_hovered and not match.winner and player:
            bg_color = PRIMARY_LIGHT
            text_color = PRIMARY_DARK
        elif is_loser:
            bg_color = OFF_WHITE
            text_color = MED_GRAY
        else:
            bg_color = OFF_WHITE
            text_color = CHARCOAL
        
        # Background with rounded corners for hover/winner
        if is_winner or (is_hovered and not match.winner and player):
            inner_rect = rect.inflate(-4, -4)
            pygame.draw.rect(self.screen, bg_color, inner_rect, border_radius=6)
        
        # Player name
        player_text = player if player else "BYE"
        player_surface = self.player_font.render(player_text, True, text_color)
        text_rect = player_surface.get_rect(center=rect.center)
        self.screen.blit(player_surface, text_rect)
        
        # Winner indicator - modern checkmark
        if is_winner:
            check_circle = pygame.Rect(rect.x + 8, rect.centery - 8, 16, 16)
            pygame.draw.circle(self.screen, WHITE, check_circle.center, 8)
            pygame.draw.circle(self.screen, ACCENT_GREEN, check_circle.center, 7)
            check_surface = self.small_font.render("✓", True, WHITE)
            check_rect = check_surface.get_rect(center=check_circle.center)
            self.screen.blit(check_surface, check_rect)
    
    def _draw_connections(self):
        for round_num in range(1, self.bracket.num_rounds):
            current_matches = self.bracket.matches[round_num - 1]
            next_matches = self.bracket.matches[round_num]
            
            round_spacing = (self.width - 100) / self.bracket.num_rounds
            start_y = self.tab_height + 120
            
            current_x = 50 + round_num * round_spacing - round_spacing / 2 + self.match_width // 2
            next_x = 50 + (round_num + 1) * round_spacing - round_spacing / 2 - self.match_width // 2
            
            current_spacing = self._get_match_spacing(len(current_matches))
            next_spacing = self._get_match_spacing(len(next_matches))
            
            for idx, next_match in enumerate(next_matches):
                next_y = start_y + 50 + idx * next_spacing + self.match_height // 2 + self.scroll_offset
                
                match1_idx = idx * 2
                match2_idx = idx * 2 + 1
                
                if match1_idx < len(current_matches):
                    match1_y = start_y + 50 + match1_idx * current_spacing + self.match_height // 2 + self.scroll_offset
                    pygame.draw.line(self.screen, BLUE, (current_x, match1_y), (next_x, next_y), 2)
                
                if match2_idx < len(current_matches):
                    match2_y = start_y + 50 + match2_idx * current_spacing + self.match_height // 2 + self.scroll_offset
                    pygame.draw.line(self.screen, BLUE, (current_x, match2_y), (next_x, next_y), 2)
    
    def _draw_close_confirmation(self):
        """Draw the close confirmation dialog."""
        # Darken background
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_rect = pygame.Rect(self.width // 2 - 200, self.height // 2 - 80, 400, 160)
        pygame.draw.rect(self.screen, WHITE, dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, BLUE, dialog_rect, 3, border_radius=10)
        
        # Message
        msg1 = self.round_font.render("Close Tournament?", True, BLACK)
        msg1_rect = msg1.get_rect(center=(self.width // 2, self.height // 2 - 40))
        self.screen.blit(msg1, msg1_rect)
        
        msg2 = self.small_font.render("Progress will be saved automatically", True, DARK_GRAY)
        msg2_rect = msg2.get_rect(center=(self.width // 2, self.height // 2 - 10))
        self.screen.blit(msg2, msg2_rect)
        
        # Yes button
        yes_button = pygame.Rect(self.width // 2 - 120, self.height // 2 + 20, 100, 40)
        pygame.draw.rect(self.screen, GREEN, yes_button, border_radius=5)
        pygame.draw.rect(self.screen, DARK_GRAY, yes_button, 2, border_radius=5)
        yes_text = self.button_font.render("Yes", True, WHITE)
        yes_text_rect = yes_text.get_rect(center=yes_button.center)
        self.screen.blit(yes_text, yes_text_rect)
        
        # No button
        no_button = pygame.Rect(self.width // 2 + 20, self.height // 2 + 20, 100, 40)
        pygame.draw.rect(self.screen, RED, no_button, border_radius=5)
        pygame.draw.rect(self.screen, DARK_GRAY, no_button, 2, border_radius=5)
        no_text = self.button_font.render("No", True, WHITE)
        no_text_rect = no_text.get_rect(center=no_button.center)
        self.screen.blit(no_text, no_text_rect)
    
    def _draw_tour_overlay(self):
        """Draw the tour overlay with current step highlighted."""
        if not self.tour_active or self.tour_step_index >= len(self.tour_steps):
            return
        
        current_step = self.tour_steps[self.tour_step_index]
        
        # Semi-transparent dark overlay over entire screen
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        
        # If there's a highlight rect, cut out that area and draw highlight border
        if current_step.highlight_rect:
            x, y, w, h = current_step.highlight_rect
            # Clear the highlighted area
            highlight_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            highlight_surface.fill((0, 0, 0, 0))
            self.screen.blit(highlight_surface, (x, y))
            
            # Draw animated pulsing border around highlight
            pulse = abs(math.sin(pygame.time.get_ticks() / 500))
            border_color = (
                int(PRIMARY[0] + (255 - PRIMARY[0]) * pulse),
                int(PRIMARY[1] + (255 - PRIMARY[1]) * pulse),
                int(PRIMARY[2] + (255 - PRIMARY[2]) * pulse)
            )
            pygame.draw.rect(self.screen, border_color, (x - 4, y - 4, w + 8, h + 8), 4, border_radius=12)
            pygame.draw.rect(self.screen, WHITE, (x - 2, y - 2, w + 4, h + 4), 2, border_radius=10)
        
        # Tour info panel at bottom
        panel_height = 220
        panel_rect = pygame.Rect(50, self.height - panel_height - 20, self.width - 100, panel_height)
        self._draw_card(panel_rect, OFF_WHITE, PRIMARY, shadow=True, glow=True)
        
        # Step counter
        step_text = self.small_font.render(
            f"Step {self.tour_step_index + 1} of {len(self.tour_steps)}",
            True, MED_GRAY
        )
        self.screen.blit(step_text, (panel_rect.x + 20, panel_rect.y + 15))
        
        # Title
        title = self.title_font.render(current_step.title, True, CHARCOAL)
        self.screen.blit(title, (panel_rect.x + 20, panel_rect.y + 45))
        
        # Description (word wrap)
        desc_y = panel_rect.y + 85
        max_width = panel_rect.width - 40
        words = current_step.description.split(' ')
        line = ""
        for word in words:
            test_line = line + word + " "
            test_surface = self.player_font.render(test_line, True, DARK_GRAY)
            if test_surface.get_width() > max_width:
                if line:
                    desc_surface = self.player_font.render(line, True, DARK_GRAY)
                    self.screen.blit(desc_surface, (panel_rect.x + 20, desc_y))
                    desc_y += 25
                line = word + " "
            else:
                line = test_line
        if line:
            desc_surface = self.player_font.render(line, True, DARK_GRAY)
            self.screen.blit(desc_surface, (panel_rect.x + 20, desc_y))
        
        # Action required text
        if current_step.action_required:
            action_y = panel_rect.y + 140
            action_text = self.small_font.render(
                f"→ {current_step.action_required}",
                True, PRIMARY
            )
            self.screen.blit(action_text, (panel_rect.x + 20, action_y))
        
        # Navigation buttons
        button_y = panel_rect.y + panel_height - 60
        button_spacing = 120
        
        # Previous button
        if self.tour_step_index > 0:
            prev_rect = pygame.Rect(panel_rect.x + 20, button_y, 100, 40)
            self._draw_button(prev_rect, "Previous", MED_GRAY, WHITE, self.button_font)
        
        # Next/Finish button
        is_last = self.tour_step_index == len(self.tour_steps) - 1
        next_text = "Finish" if is_last else "Next"
        next_rect = pygame.Rect(panel_rect.x + 140, button_y, 100, 40)
        self._draw_button(next_rect, next_text, PRIMARY, WHITE, self.button_font)
        
        # Skip tour button
        skip_rect = pygame.Rect(panel_rect.right - 120, button_y, 100, 40)
        self._draw_button(skip_rect, "Skip Tour", ACCENT_RED, WHITE, self.button_font)
    
    def _handle_tour_click(self, pos: Tuple[int, int]) -> bool:
        """Handle clicks on tour overlay. Returns True if click was handled."""
        if not self.tour_active:
            return False
        
        mx, my = pos
        panel_height = 220
        panel_rect = pygame.Rect(50, self.height - panel_height - 20, self.width - 100, panel_height)
        button_y = panel_rect.y + panel_height - 60
        
        # Previous button
        if self.tour_step_index > 0:
            prev_rect = pygame.Rect(panel_rect.x + 20, button_y, 100, 40)
            if prev_rect.collidepoint(mx, my):
                self.prev_tour_step()
                return True
        
        # Next/Finish button
        next_rect = pygame.Rect(panel_rect.x + 140, button_y, 100, 40)
        if next_rect.collidepoint(mx, my):
            self.next_tour_step()
            return True
        
        # Skip tour button
        skip_rect = pygame.Rect(panel_rect.right - 120, button_y, 100, 40)
        if skip_rect.collidepoint(mx, my):
            self.end_tour()
            return True
        
        # Click outside panel - allow interaction with highlighted area
        if current_step := self.tour_steps[self.tour_step_index]:
            if current_step.highlight_rect:
                x, y, w, h = current_step.highlight_rect
                if x <= mx <= x + w and y <= my <= y + h:
                    return False  # Allow click through to highlighted element
        
        return True  # Block all other clicks
    
    def _draw_instructions(self):
        instructions = [
            "Click on a match, then click a player to select winner",
            "Press H to hide/show instructions",
            "Press ESC to cancel selection",
            "Scroll to navigate | Auto-saves progress"
        ]
        
        y = self.height - 100
        for instruction in instructions:
            text_surface = self.small_font.render(instruction, True, DARK_GRAY)
            text_rect = text_surface.get_rect(center=(self.width // 2, y))
            self.screen.blit(text_surface, text_rect)
            y += 22
    
    def _draw_selection_prompt(self):
        round_num, match_idx = self.selected_match
        match = self.bracket.matches[round_num - 1][match_idx]
        
        if not match.winner and match.player1 and match.player2:
            prompt = f"Select winner: {match.player1} or {match.player2}"
            prompt_surface = self.round_font.render(prompt, True, ORANGE)
            prompt_rect = prompt_surface.get_rect(center=(self.width // 2, 90))
            
            bg_rect = prompt_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, WHITE, bg_rect, border_radius=5)
            pygame.draw.rect(self.screen, ORANGE, bg_rect, 2, border_radius=5)
            
            self.screen.blit(prompt_surface, prompt_rect)
    
    def create_new_tournament(self, name: str, location: str, date_scheduled: str, time_scheduled: str):
        """Create a new tournament."""
        tournament_id = str(uuid.uuid4())
        metadata = TournamentMetadata(
            id=tournament_id,
            name=name,
            location=location,
            date_scheduled=date_scheduled,
            time_scheduled=time_scheduled,
            date_created=datetime.now().isoformat()
        )
        
        self.current_tournament_id = tournament_id
        self.current_metadata = metadata
        self.editing_players = []
        self.initial_participants = []
        self.bracket = None
        self.selected_match = None
        self.scroll_offset = 0
        
        self.save_current_tournament()
        self.active_tab = "Current Tournament"
    
    def reset_tournament(self):
        """Reset the tournament to initial state."""
        if self.editing_players:
            self.bracket = TournamentBracket(self.editing_players)
            self._recalculate_scaling()
            self.selected_match = None
            self.scroll_offset = 0
            self.save_current_tournament()
    
    def reshuffle_tournament(self):
        """Reshuffle participants and reset tournament."""
        if self.editing_players:
            shuffled = self.editing_players.copy()
            random.shuffle(shuffled)
            self.editing_players = shuffled
            self.bracket = TournamentBracket(shuffled)
            self._recalculate_scaling()
            self.selected_match = None
            self.scroll_offset = 0
            self.save_current_tournament()
    
    def generate_bracket(self):
        """Generate bracket from current player list."""
        if self.editing_players:
            self.bracket = TournamentBracket(self.editing_players)
            self._recalculate_scaling()
            self.initial_participants = self.editing_players.copy()
            self.selected_match = None
            self.scroll_offset = 0
            self.save_current_tournament()
            self.active_tab = "Bracket"
    
    def save_current_tournament(self):
        """Save current tournament state to disk."""
        if not self.current_tournament_id or not self.current_metadata:
            return
        
        try:
            data = {
                "metadata": self.current_metadata.to_dict(),
                "participants": self.editing_players,
                "bracket": self.bracket.to_dict() if self.bracket else None
            }
            
            filepath = self.tournaments_dir / f"{self.current_tournament_id}.json"
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving tournament: {e}")
    
    def load_tournament(self, tournament_id: str):
        """Load a specific tournament."""
        try:
            filepath = self.tournaments_dir / f"{tournament_id}.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                self.current_tournament_id = tournament_id
                self.current_metadata = TournamentMetadata.from_dict(data["metadata"])
                self.editing_players = data.get("participants", [])
                self.initial_participants = self.editing_players.copy()
                
                if data.get("bracket"):
                    self.bracket = TournamentBracket.from_dict(data["bracket"])
                else:
                    self.bracket = None
                
                self._recalculate_scaling()
                self.active_tab = "Current Tournament"
                print(f"Loaded tournament: {self.current_metadata.name}")
        except Exception as e:
            print(f"Error loading tournament: {e}")
    
    def _initialize_tour_steps(self):
        """Initialize the user tour with all feature highlights."""
        self.tour_steps = [
            TourStep(
                id="welcome",
                title="Welcome to Tournament Manager!",
                description="This tour will walk you through all the features. Press T to start the tour anytime, or ESC to skip.",
                tab="Tournaments",
                highlight_rect=None,
                action_required="Click 'Next' to continue"
            ),
            TourStep(
                id="create_tournament",
                title="Creating Tournaments",
                description="Click the 'Create New Tournament' button to create a tournament. Each tournament has a name, location, and scheduled date/time.",
                tab="Tournaments",
                highlight_rect=(self.width // 2 - 120, self.height - 80, 240, 50),
                action_required="Create a tournament to continue"
            ),
            TourStep(
                id="tournament_list",
                title="Tournament List",
                description="All your tournaments are listed here. Click any tournament to view and edit it.",
                tab="Tournaments",
                highlight_rect=(100, self.tab_height + 120, self.width - 200, 300),
                action_required="Select a tournament to continue"
            ),
            TourStep(
                id="edit_tournament_info",
                title="Editable Tournament Details",
                description="You can edit the tournament name, location, date, and time by clicking on them. Notice the edit icons (✎) indicating editable fields.",
                tab="Current Tournament",
                highlight_rect=(100, self.tab_height + 80, 800, 180),
                action_required="Try editing a field (optional)"
            ),
            TourStep(
                id="add_players",
                title="Managing Players",
                description="Add players to your tournament here. Type a name and press Enter or click 'Add Player'. You can also remove players with the X button.",
                tab="Player List",
                highlight_rect=(self.width // 2 - 250, self.tab_height + 120, 500, 400),
                action_required="Add at least 2 players to continue"
            ),
            TourStep(
                id="generate_bracket",
                title="Generate Bracket",
                description="Once you have at least 2 players, click 'Generate Bracket' to create the tournament structure. Byes are automatically assigned if needed.",
                tab="Player List",
                highlight_rect=(self.width // 2 - 120, self.height - 60, 240, 50),
                action_required="Generate the bracket"
            ),
            TourStep(
                id="view_bracket",
                title="Tournament Bracket",
                description="Here's your tournament bracket! Click on a match to select it, then click a player's name to declare them the winner. Winners advance automatically.",
                tab="Bracket",
                highlight_rect=(50, self.tab_height + 120, self.width - 100, 400),
                action_required="Select a match and choose a winner"
            ),
            TourStep(
                id="match_selection",
                title="Match Interaction",
                description="Selected matches are highlighted with a blue glow. Only matches with both players can have winners declared. Winners get green checkmarks.",
                tab="Bracket",
                highlight_rect=None,
                action_required="Try selecting different matches"
            ),
            TourStep(
                id="final_results",
                title="Final Results",
                description="Once the tournament is complete, view the final standings here. The champion is highlighted in gold!",
                tab="Final Results",
                highlight_rect=(self.width // 2 - 150, self.tab_height + 80, 300, 500),
                action_required=None
            ),
            TourStep(
                id="dangerous_operations",
                title="Dangerous Operations",
                description="The 'Dangerous Operations' panel on the Current Tournament tab lets you reset (clear all winners) or reshuffle (regenerate with same players).",
                tab="Current Tournament",
                highlight_rect=(100, self.tab_height + 450, self.width - 200, 150),
                action_required=None
            ),
            TourStep(
                id="auto_save",
                title="Automatic Saving",
                description="All changes are automatically saved! Your tournaments, players, and match results persist between sessions.",
                tab="Current Tournament",
                highlight_rect=None,
                action_required=None
            ),
            TourStep(
                id="keyboard_shortcuts",
                title="Keyboard Shortcuts",
                description="Press H on the Bracket tab to toggle instructions. Press T anytime to restart this tour. Press ESC to cancel editing or close dialogs.",
                tab="Bracket",
                highlight_rect=None,
                action_required=None
            ),
            TourStep(
                id="tour_complete",
                title="Tour Complete!",
                description="You've learned all the features! Press T anytime to replay this tour. Happy bracketing!",
                tab="Tournaments",
                highlight_rect=None,
                action_required="Click 'Finish' to end tour"
            )
        ]
    
    def start_tour(self):
        """Start the user tour."""
        self.tour_active = True
        self.tour_step_index = 0
        # Switch to the first step's tab
        if self.tour_steps:
            self.active_tab = self.tour_steps[0].tab
    
    def next_tour_step(self):
        """Advance to the next tour step."""
        if self.tour_step_index < len(self.tour_steps) - 1:
            self.tour_step_index += 1
            # Switch to the new step's tab
            current_step = self.tour_steps[self.tour_step_index]
            self.active_tab = current_step.tab
        else:
            # Tour complete
            self.end_tour()
    
    def prev_tour_step(self):
        """Go back to the previous tour step."""
        if self.tour_step_index > 0:
            self.tour_step_index -= 1
            # Switch to the new step's tab
            current_step = self.tour_steps[self.tour_step_index]
            self.active_tab = current_step.tab
    
    def end_tour(self):
        """End the user tour."""
        self.tour_active = False
        self.tour_step_index = 0
    
    def load_tournaments_list(self):
        """Load list of all tournaments."""
        self.tournaments_list = []
        
        try:
            for filepath in self.tournaments_dir.glob("*.json"):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    metadata = TournamentMetadata.from_dict(data["metadata"])
                    self.tournaments_list.append(metadata)
            
            # Sort by date created (newest first)
            self.tournaments_list.sort(key=lambda x: x.date_created, reverse=True)
        except Exception as e:
            print(f"Error loading tournaments list: {e}")
    
    def delete_tournament(self, tournament_id: str):
        """Delete a tournament."""
        try:
            filepath = self.tournaments_dir / f"{tournament_id}.json"
            if filepath.exists():
                filepath.unlink()
                self.load_tournaments_list()
                
                if self.current_tournament_id == tournament_id:
                    self.current_tournament_id = None
                    self.current_metadata = None
                    self.editing_players = []
                    self.bracket = None
                    self.active_tab = "Tournaments"
        except Exception as e:
            print(f"Error deleting tournament: {e}")
    
    def _handle_click(self, pos: Tuple[int, int]):
        mx, my = pos
        
        # Check close button
        if self.close_button_rect.collidepoint(mx, my):
            self.show_close_confirm = True
            return
        
        # Check close confirmation dialog
        if self.show_close_confirm:
            dialog_rect = pygame.Rect(self.width // 2 - 200, self.height // 2 - 80, 400, 160)
            yes_button = pygame.Rect(self.width // 2 - 120, self.height // 2 + 20, 100, 40)
            no_button = pygame.Rect(self.width // 2 + 20, self.height // 2 + 20, 100, 40)
            
            if yes_button.collidepoint(mx, my):
                self.save_current_tournament()
                pygame.quit()
                sys.exit()
            elif no_button.collidepoint(mx, my):
                self.show_close_confirm = False
            return
        
        # Current Tournament tab interactions
        if self.active_tab == "Current Tournament":
            # Check editable field clicks (only if we have a tournament)
            if self.current_metadata:
                y_offset = self.tab_height + 80
                
                # Tournament name field
                name_rect = pygame.Rect(300, y_offset - 8, 500, 40)
                if name_rect.collidepoint(mx, my):
                    self.active_input_field = "tournament_name"
                    self.input_text = self.current_metadata.name
                    return
                y_offset += 60
                
                # Location field
                location_rect = pygame.Rect(300, y_offset - 8, 500, 40)
                if location_rect.collidepoint(mx, my):
                    self.active_input_field = "tournament_location"
                    self.input_text = self.current_metadata.location
                    return
                y_offset += 60
                
                # Date field
                date_rect = pygame.Rect(300, y_offset - 8, 250, 40)
                if date_rect.collidepoint(mx, my):
                    self.active_input_field = "tournament_date"
                    self.input_text = self.current_metadata.date_scheduled
                    return
                
                # Time field
                time_rect = pygame.Rect(570, y_offset - 8, 230, 40)
                if time_rect.collidepoint(mx, my):
                    self.active_input_field = "tournament_time"
                    self.input_text = self.current_metadata.time_scheduled
                    return
                
                # Click outside editable fields - save and deactivate
                if self.active_input_field:
                    # Save the edited value
                    if self.active_input_field == "tournament_name":
                        self.current_metadata.name = self.input_text
                    elif self.active_input_field == "tournament_location":
                        self.current_metadata.location = self.input_text
                    elif self.active_input_field == "tournament_date":
                        self.current_metadata.date_scheduled = self.input_text
                    elif self.active_input_field == "tournament_time":
                        self.current_metadata.time_scheduled = self.input_text
                    
                    self.active_input_field = None
                    self.input_text = ""
                    self.save_current_tournament()
            
            # Check dangerous operations panel toggle
            panel_toggle_rect = pygame.Rect(100, self.tab_height + 450, self.width - 200, 40)
            if panel_toggle_rect.collidepoint(mx, my):
                self.dangerous_panel_open = not self.dangerous_panel_open
                return
            
            # If panel is open, check for button clicks
            if self.dangerous_panel_open:
                reset_button_rect = pygame.Rect(self.width // 2 - 220, self.tab_height + 520, 200, 50)
                reshuffle_button_rect = pygame.Rect(self.width // 2 + 20, self.tab_height + 520, 200, 50)
                
                if reset_button_rect.collidepoint(mx, my):
                    self.reset_tournament()
                    return
                elif reshuffle_button_rect.collidepoint(mx, my):
                    self.reshuffle_tournament()
                    return
        
        # Player List tab interactions
        elif self.active_tab == "Player List":
            # Add player button
            add_button_rect = pygame.Rect(self.width // 2 - 100, self.height - 120, 200, 50)
            if add_button_rect.collidepoint(mx, my) and self.new_player_name.strip():
                self.editing_players.append(self.new_player_name.strip())
                self.new_player_name = ""
                self._recalculate_scaling()
                self.save_current_tournament()
                return
            
            # Generate bracket button
            generate_button_rect = pygame.Rect(self.width // 2 - 120, self.height - 60, 240, 50)
            if generate_button_rect.collidepoint(mx, my) and len(self.editing_players) >= 2:
                self.generate_bracket()
                return
            
            # Remove player buttons (small X next to each player)
            y_offset = self.tab_height + 180
            for i in range(len(self.editing_players)):
                remove_btn = pygame.Rect(self.width // 2 + 180, y_offset + i * 35, 30, 30)
                if remove_btn.collidepoint(mx, my):
                    self.editing_players.pop(i)
                    self._recalculate_scaling()
                    self.save_current_tournament()
                    return
            return
        
        # Tournaments tab interactions
        elif self.active_tab == "Tournaments":
            # Create new tournament button
            create_button_rect = pygame.Rect(self.width // 2 - 120, self.height - 80, 240, 50)
            if create_button_rect.collidepoint(mx, my):
                # For now, create with default values - could add a dialog later
                import datetime
                today = datetime.date.today()
                self.create_new_tournament(
                    f"Tournament {len(self.tournaments_list) + 1}",
                    "TBD",
                    today.isoformat(),
                    "12:00"
                )
                return
            
            # Click on tournament to load it
            y_offset = self.tab_height + 120
            for i, tournament in enumerate(self.tournaments_list):
                tournament_rect = pygame.Rect(100, y_offset + i * 80, self.width - 200, 70)
                if tournament_rect.collidepoint(mx, my):
                    self.load_tournament(tournament.id)
                    return
            return
        
        # Only handle bracket interactions on Bracket tab
        if self.active_tab != "Bracket" or not self.bracket:
            return
        
        if self.selected_match:
            round_num, match_idx = self.selected_match
            match = self.bracket.matches[round_num - 1][match_idx]
            
            if not match.winner and match.player1 and match.player2:
                round_spacing = (self.width - 100) / self.bracket.num_rounds
                start_y = self.tab_height + 120
                
                x = 50 + round_num * round_spacing - round_spacing / 2
                num_matches = len(self.bracket.matches[round_num - 1])
                match_spacing = self._get_match_spacing(num_matches)
                y = start_y + 50 + match_idx * match_spacing + self.scroll_offset
                
                box_rect = pygame.Rect(
                    x - self.match_width // 2,
                    y,
                    self.match_width,
                    self.match_height
                )
                
                if box_rect.collidepoint(mx, my):
                    relative_y = my - box_rect.y
                    if relative_y < self.player_height and match.player1:
                        self.bracket.set_match_winner(round_num, match_idx, match.player1)
                        self.selected_match = None
                        self.save_current_tournament()
                    elif relative_y >= self.player_height and match.player2:
                        self.bracket.set_match_winner(round_num, match_idx, match.player2)
                        self.selected_match = None
                        self.save_current_tournament()
                    return
        
        for round_num, round_matches in enumerate(self.bracket.matches, 1):
            round_spacing = (self.width - 100) / self.bracket.num_rounds
            start_y = self.tab_height + 120
            
            x = 50 + round_num * round_spacing - round_spacing / 2
            num_matches = len(round_matches)
            match_spacing = self._get_match_spacing(num_matches)
            
            for idx, match in enumerate(round_matches):
                y = start_y + 50 + idx * match_spacing + self.scroll_offset
                
                box_rect = pygame.Rect(
                    x - self.match_width // 2,
                    y,
                    self.match_width,
                    self.match_height
                )
                
                if box_rect.collidepoint(mx, my):
                    if not match.winner and match.player1 and match.player2:
                        self.selected_match = (round_num, idx)
                    return
    
    def _handle_hover(self, pos: Tuple[int, int]):
        mx, my = pos
        self.hovered_player = None
        
        # Check if hovering over close button
        self.hovered_close_button = self.close_button_rect.collidepoint(mx, my)
        
        if self.selected_match:
            round_num, match_idx = self.selected_match
            match = self.bracket.matches[round_num - 1][match_idx]
            
            if not match.winner and match.player1 and match.player2:
                round_spacing = (self.width - 100) / self.bracket.num_rounds
                start_y = self.tab_height + 120
                
                x = 50 + round_num * round_spacing - round_spacing / 2
                num_matches = len(self.bracket.matches[round_num - 1])
                match_spacing = self._get_match_spacing(num_matches)
                y = start_y + 50 + match_idx * match_spacing + self.scroll_offset
                
                box_rect = pygame.Rect(
                    x - self.match_width // 2,
                    y,
                    self.match_width,
                    self.match_height
                )
                
                if box_rect.collidepoint(mx, my):
                    relative_y = my - box_rect.y
                    if relative_y < self.player_height:
                        self.hovered_player = (round_num, match_idx, 1)
                    else:
                        self.hovered_player = (round_num, match_idx, 2)


if __name__ == "__main__":
    print("Starting Tournament Manager...")
    print("Instructions:")
    print("- Create or load tournaments from the Tournaments tab")
    print("- Add players in the Player List tab")
    print("- Generate bracket to start the tournament")
    print("- Click on matches to select winners")
    print("- Press H to toggle instructions on Bracket tab")
    print("- Progress is automatically saved")
    print("\nStarting GUI...")
    
    gui = TournamentBracketGUI()
    gui.run()

