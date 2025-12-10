"""
Screenshot capture utility for Tournament Manager.
Automatically captures screenshots of all modes using pygame.
"""

import pygame
import sys
import os
from pathlib import Path
from tournament import TournamentBracketGUI
import time
from datetime import datetime

def auto_capture_all_screenshots():
    """Automatically capture screenshots of all major app states."""
    print("Automated Screenshot Capture")
    print("=" * 50)
    print("This will automatically capture screenshots of all app modes.")
    print("You'll have a few seconds between each capture to set up the view.\n")
    
    gui = TournamentBracketGUI(width=1400, height=800)
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    clock = pygame.time.Clock()
    
    # Define all screenshots to capture
    captures = [
        {
            "filename": "01_tournaments_list.png",
            "tab": "Tournaments",
            "description": "Tournament List - showing all tournaments",
            "setup": lambda g: (setattr(g, 'active_tab', 'Tournaments'), None)[1],
            "wait": 1.5
        },
        {
            "filename": "02_tournament_details.png",
            "tab": "Current Tournament",
            "description": "Tournament Details with editable fields",
            "setup": lambda g: (
                g.create_new_tournament("Championship 2026", "Main Arena", "2026-03-15", "14:00") 
                if not g.current_metadata else None,
                setattr(g, 'active_tab', 'Current Tournament')
            )[1],
            "wait": 1.5
        },
        {
            "filename": "03_player_list.png",
            "tab": "Player List",
            "description": "Player List management interface",
            "setup": lambda g: (
                setattr(g, 'active_tab', 'Player List'),
                g.editing_players.extend(["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]) 
                if len(g.editing_players) == 0 else None
            )[1],
            "wait": 1.5
        },
        {
            "filename": "04_bracket_empty.png",
            "tab": "Bracket",
            "description": "Empty bracket after generation",
            "setup": lambda g: (
                g.generate_bracket() if not g.bracket else None,
                setattr(g, 'active_tab', 'Bracket')
            )[1],
            "wait": 1.5
        },
        {
            "filename": "05_match_selected.png",
            "tab": "Bracket",
            "description": "Match selected with blue glow",
            "setup": lambda g: (
                setattr(g, 'selected_match', (1, 0)),
                setattr(g, 'active_tab', 'Bracket')
            )[1],
            "wait": 1.5
        },
        {
            "filename": "06_winner_declared.png",
            "tab": "Bracket",
            "description": "Winner declared with green checkmark",
            "setup": lambda g: (
                g.bracket.set_match_winner(1, 0, g.bracket.matches[0][0].player1) 
                if g.bracket and g.bracket.matches[0][0].player1 and g.bracket.matches[0][0].player2 else None,
                setattr(g, 'active_tab', 'Bracket')
            )[1],
            "wait": 1.5
        },
        {
            "filename": "07_tournament_progress.png",
            "tab": "Bracket",
            "description": "Tournament in progress with multiple winners",
            "setup": lambda g: (
                g.bracket.set_match_winner(1, 1, g.bracket.matches[0][1].player1)
                if g.bracket and len(g.bracket.matches[0]) > 1 
                and g.bracket.matches[0][1].player1 
                and g.bracket.matches[0][1].player2 else None,
                setattr(g, 'active_tab', 'Bracket')
            )[1],
            "wait": 1.5
        },
        {
            "filename": "08_final_results.png",
            "tab": "Final Results",
            "description": "Final results with champion highlighted",
            "setup": lambda g: (
                setattr(g, 'active_tab', 'Final Results')
            ),
            "wait": 1.5
        },
        {
            "filename": "09_tour_welcome.png",
            "tab": "Tournaments",
            "description": "Tour mode welcome screen",
            "setup": lambda g: (
                g.start_tour()
            ),
            "wait": 2.0
        },
        {
            "filename": "10_tour_highlight.png",
            "tab": None,  # Tour controls tab
            "description": "Tour mode with pulsing highlight",
            "setup": lambda g: (
                g.next_tour_step() if g.tour_active else g.start_tour(),
                g.next_tour_step()
            )[1],
            "wait": 2.0
        },
        {
            "filename": "11_edit_mode.png",
            "tab": "Current Tournament",
            "description": "Active editing mode on tournament field",
            "setup": lambda g: (
                g.end_tour() if g.tour_active else None,
                setattr(g, 'active_tab', 'Current Tournament'),
                setattr(g, 'active_input_field', 'tournament_name'),
                setattr(g, 'input_text', 'Championship 2026')
            )[1],
            "wait": 1.5
        },
        {
            "filename": "12_dangerous_operations.png",
            "tab": "Current Tournament",
            "description": "Dangerous operations panel expanded",
            "setup": lambda g: (
                setattr(g, 'active_input_field', None),
                setattr(g, 'active_tab', 'Current Tournament'),
                setattr(g, 'dangerous_panel_open', True)
            )[1],
            "wait": 1.5
        },
        {
            "filename": "13_glassmorphism.png",
            "tab": "Current Tournament",
            "description": "Modern UI with glassmorphism effects",
            "setup": lambda g: (
                setattr(g, 'dangerous_panel_open', False),
                setattr(g, 'active_tab', 'Current Tournament')
            )[1],
            "wait": 1.5
        }
    ]
    
    for i, capture in enumerate(captures, 1):
        print(f"\n[{i}/{len(captures)}] Capturing: {capture['description']}")
        
        # Setup the view
        if capture['setup']:
            capture['setup'](gui)
        
        # Allow UI to update
        for _ in range(int(capture['wait'] * 60)):  # 60 FPS
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            gui._draw()
            pygame.display.flip()
            clock.tick(60)
        
        # Capture screenshot
        filepath = screenshots_dir / capture['filename']
        pygame.image.save(gui.screen, str(filepath))
        print(f"   ✓ Saved: {filepath}")
    
    # Close tour if active
    gui.end_tour()
    
    print("\n" + "=" * 50)
    print("Screenshot capture complete!")
    print(f"All {len(captures)} screenshots saved to ./screenshots/")
    print("\nYou can now:")
    print("1. Review screenshots in ./screenshots/")
    print("2. Commit and push to GitHub:")
    print("   git add screenshots/")
    print("   git commit -m 'Add application screenshots'")
    print("   git push")
    
    # Show the final screen for a moment
    for _ in range(120):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        gui._draw()
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    auto_capture_all_screenshots()
