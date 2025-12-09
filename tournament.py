from typing import List, Optional, Tuple
from dataclasses import dataclass
import math
import pygame
import sys


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (240, 240, 240)
DARK_GRAY = (100, 100, 100)
BLUE = (70, 130, 220)
LIGHT_BLUE = (135, 206, 250)
GREEN = (60, 179, 113)
GOLD = (255, 215, 0)
ORANGE = (255, 165, 0)
RED = (220, 60, 60)
BUTTON_COLOR = (70, 130, 220)
BUTTON_HOVER = (100, 160, 250)


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


class TournamentBracketGUI:
    """Interactive pygame GUI for tournament brackets."""
    
    def __init__(self, bracket: TournamentBracket, initial_participants: List[str], width: int = 1400, height: int = 800):
        pygame.init()
        
        self.bracket = bracket
        self.initial_participants = initial_participants
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Tournament Bracket")
        
        # Calculate scaling based on number of participants
        self.num_participants = len(initial_participants)
        self.num_rounds = bracket.num_rounds
        
        # Scale fonts based on participant count
        if self.num_participants <= 8:
            title_size, round_size, player_size, small_size, button_size = 48, 32, 24, 20, 28
            self.match_width, self.match_height = 200, 80
        elif self.num_participants <= 16:
            title_size, round_size, player_size, small_size, button_size = 42, 28, 20, 18, 24
            self.match_width, self.match_height = 180, 70
        elif self.num_participants <= 32:
            title_size, round_size, player_size, small_size, button_size = 36, 24, 18, 16, 22
            self.match_width, self.match_height = 160, 60
        else:
            title_size, round_size, player_size, small_size, button_size = 32, 20, 16, 14, 20
            self.match_width, self.match_height = 140, 50
        
        self.title_font = pygame.font.Font(None, title_size)
        self.round_font = pygame.font.Font(None, round_size)
        self.player_font = pygame.font.Font(None, player_size)
        self.small_font = pygame.font.Font(None, small_size)
        self.button_font = pygame.font.Font(None, button_size)
        
        self.player_height = self.match_height // 2 - 5
        
        self.selected_match: Optional[Tuple[int, int]] = None
        self.hovered_player: Optional[Tuple[int, int, int]] = None
        self.hovered_button = False
        
        self.scroll_offset = 0
        self.show_instructions = True
        
        # Reset button
        self.reset_button_rect = pygame.Rect(self.width - 150, 20, 130, 40)
        
        self.clock = pygame.time.Clock()
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self._handle_click(event.pos)
                    elif event.button == 4:
                        self.scroll_offset = min(0, self.scroll_offset + 30)
                    elif event.button == 5:
                        self.scroll_offset -= 30
                elif event.type == pygame.MOUSEMOTION:
                    self._handle_hover(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.selected_match = None
                    elif event.key == pygame.K_h:
                        self.show_instructions = not self.show_instructions
                    elif event.key == pygame.K_r:
                        self.reset_tournament()
            
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def _draw(self):
        self.screen.fill(LIGHT_GRAY)
        
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
        
        # Draw reset button
        self._draw_reset_button()
        
        self._draw_rounds()
        self._draw_connections()
        
        if self.show_instructions:
            self._draw_instructions()
        
        if self.selected_match:
            self._draw_selection_prompt()
    
    def _draw_rounds(self):
        num_rounds = self.bracket.num_rounds
        round_spacing = (self.width - 100) / num_rounds
        start_y = 120
        
        for round_num, round_matches in enumerate(self.bracket.matches, 1):
            x = 50 + round_num * round_spacing - round_spacing / 2
            
            round_name = self.bracket._get_round_name(round_num)
            round_surface = self.round_font.render(round_name, True, BLUE)
            round_rect = round_surface.get_rect(center=(x, start_y))
            self.screen.blit(round_surface, round_rect)
            
            num_matches = len(round_matches)
            available_height = self.height - start_y - 150
            match_spacing = available_height / max(num_matches, 1)
            
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
        
        shadow_rect = box_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(self.screen, DARK_GRAY, shadow_rect, border_radius=8)
        
        border_color = ORANGE if is_selected else BLUE
        pygame.draw.rect(self.screen, WHITE, box_rect, border_radius=8)
        pygame.draw.rect(self.screen, border_color, box_rect, 3, border_radius=8)
        
        player1_rect = pygame.Rect(box_rect.x, box_rect.y, box_rect.width, self.player_height)
        player2_rect = pygame.Rect(box_rect.x, box_rect.y + self.player_height, box_rect.width, self.player_height)
        
        self._draw_player(match, player1_rect, match.player1, 1, round_num, match_idx)
        
        pygame.draw.line(
            self.screen,
            GRAY,
            (box_rect.x, box_rect.y + self.player_height),
            (box_rect.x + box_rect.width, box_rect.y + self.player_height),
            2
        )
        
        self._draw_player(match, player2_rect, match.player2, 2, round_num, match_idx)
        
        match_num_surface = self.small_font.render(f"M{match.match_id + 1}", True, DARK_GRAY)
        self.screen.blit(match_num_surface, (box_rect.x + 5, box_rect.y + box_rect.height - 18))
    
    def _draw_player(self, match: Match, rect: pygame.Rect, player: Optional[str], 
                     player_num: int, round_num: int, match_idx: int):
        is_hovered = self.hovered_player == (round_num, match_idx, player_num)
        is_winner = player and match.winner == player
        is_loser = player and match.winner and match.winner != player
        
        if is_winner:
            bg_color = GREEN
        elif is_hovered and not match.winner and player:
            bg_color = LIGHT_BLUE
        else:
            bg_color = WHITE
        
        if is_winner or (is_hovered and not match.winner and player):
            pygame.draw.rect(self.screen, bg_color, rect)
        
        player_text = player if player else "BYE"
        text_color = WHITE if is_winner else (DARK_GRAY if is_loser else BLACK)
        
        player_surface = self.player_font.render(player_text, True, text_color)
        text_rect = player_surface.get_rect(center=rect.center)
        self.screen.blit(player_surface, text_rect)
        
        if is_winner:
            check_surface = self.player_font.render("X", True, WHITE)
            self.screen.blit(check_surface, (rect.x + 5, rect.y + 5))
    
    def _draw_connections(self):
        for round_num in range(1, self.bracket.num_rounds):
            current_matches = self.bracket.matches[round_num - 1]
            next_matches = self.bracket.matches[round_num]
            
            round_spacing = (self.width - 100) / self.bracket.num_rounds
            start_y = 120
            
            current_x = 50 + round_num * round_spacing - round_spacing / 2 + self.match_width // 2
            next_x = 50 + (round_num + 1) * round_spacing - round_spacing / 2 - self.match_width // 2
            
            available_height = self.height - start_y - 150
            current_spacing = available_height / max(len(current_matches), 1)
            next_spacing = available_height / max(len(next_matches), 1)
            
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
    
    def _draw_reset_button(self):
        """Draw the reset button."""
        button_color = BUTTON_HOVER if self.hovered_button else BUTTON_COLOR
        
        # Shadow
        shadow_rect = self.reset_button_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pygame.draw.rect(self.screen, DARK_GRAY, shadow_rect, border_radius=5)
        
        # Button
        pygame.draw.rect(self.screen, button_color, self.reset_button_rect, border_radius=5)
        pygame.draw.rect(self.screen, WHITE, self.reset_button_rect, 2, border_radius=5)
        
        # Text
        text_surface = self.button_font.render("Reset (R)", True, WHITE)
        text_rect = text_surface.get_rect(center=self.reset_button_rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def _draw_instructions(self):
        instructions = [
            "Click on a match, then click a player to select winner",
            "Press H to hide/show instructions | Press R to reset",
            "Press ESC to cancel selection",
            "Scroll to navigate"
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
    
    def reset_tournament(self):
        """Reset the tournament to initial state."""
        self.bracket = TournamentBracket(self.initial_participants)
        self.selected_match = None
        self.scroll_offset = 0
    
    def _handle_click(self, pos: Tuple[int, int]):
        mx, my = pos
        
        # Check if clicking reset button
        if self.reset_button_rect.collidepoint(mx, my):
            self.reset_tournament()
            return
        
        if self.selected_match:
            round_num, match_idx = self.selected_match
            match = self.bracket.matches[round_num - 1][match_idx]
            
            if not match.winner and match.player1 and match.player2:
                round_spacing = (self.width - 100) / self.bracket.num_rounds
                start_y = 120
                
                x = 50 + round_num * round_spacing - round_spacing / 2
                num_matches = len(self.bracket.matches[round_num - 1])
                available_height = self.height - start_y - 150
                match_spacing = available_height / max(num_matches, 1)
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
                    elif relative_y >= self.player_height and match.player2:
                        self.bracket.set_match_winner(round_num, match_idx, match.player2)
                        self.selected_match = None
                    return
        
        for round_num, round_matches in enumerate(self.bracket.matches, 1):
            round_spacing = (self.width - 100) / self.bracket.num_rounds
            start_y = 120
            
            x = 50 + round_num * round_spacing - round_spacing / 2
            num_matches = len(round_matches)
            available_height = self.height - start_y - 150
            match_spacing = available_height / max(num_matches, 1)
            
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
        
        # Check if hovering over reset button
        self.hovered_button = self.reset_button_rect.collidepoint(mx, my)
        
        if self.selected_match:
            round_num, match_idx = self.selected_match
            match = self.bracket.matches[round_num - 1][match_idx]
            
            if not match.winner and match.player1 and match.player2:
                round_spacing = (self.width - 100) / self.bracket.num_rounds
                start_y = 120
                
                x = 50 + round_num * round_spacing - round_spacing / 2
                num_matches = len(self.bracket.matches[round_num - 1])
                available_height = self.height - start_y - 150
                match_spacing = available_height / max(num_matches, 1)
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
    # Generate 32 participants
    participants = [f"Player {i+1}" for i in range(32)]
    
    print("Creating interactive tournament bracket...")
    print("Instructions:")
    print("- Click on a match to select it")
    print("- Click on a player name to select them as the winner")
    print("- Press H to toggle instructions")
    print("- Press R or click Reset button to restart tournament")
    print("- Press ESC to cancel selection")
    print("\nStarting GUI with 32 participants...")
    
    bracket = TournamentBracket(participants)
    gui = TournamentBracketGUI(bracket, participants)
    gui.run()
