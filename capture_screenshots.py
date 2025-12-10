"""
Screenshot capture utility for Tournament Manager.
Run this script to automatically capture screenshots of all modes.
"""

import pygame
import sys
import os
from pathlib import Path
from tournament import TournamentBracketGUI
import time

def capture_screenshot(screen, filename):
    """Save a screenshot of the current screen."""
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    filepath = screenshots_dir / filename
    pygame.image.save(screen, str(filepath))
    print(f"Saved: {filepath}")

def main():
    """Capture screenshots of all app modes."""
    print("Starting screenshot capture...")
    print("Please interact with the app to move through different states.")
    print("Press SPACE to capture a screenshot, Q to quit.\n")
    
    gui = TournamentBracketGUI(width=1400, height=800)
    clock = pygame.time.Clock()
    running = True
    screenshot_count = 0
    
    # Suggested screenshots to capture
    instructions = [
        "1. Tournaments List Tab - Press SPACE to capture",
        "2. Create Tournament Dialog - Press SPACE",
        "3. Current Tournament Tab - Press SPACE",
        "4. Editable Field (click on a field) - Press SPACE",
        "5. Player List Tab - Press SPACE",
        "6. Adding Players - Press SPACE",
        "7. Bracket Tab (empty) - Press SPACE",
        "8. Bracket Tab (with matches) - Press SPACE",
        "9. Match Selected - Press SPACE",
        "10. Winner Declared - Press SPACE",
        "11. Final Results Tab - Press SPACE",
        "12. Tour Mode (Press T first) - Press SPACE",
        "13. Tour Highlight Example - Press SPACE",
    ]
    
    print("Suggested screenshots:")
    for instruction in instructions:
        print(f"  {instruction}")
    print("\nNavigate through the app and press SPACE for each screenshot.")
    print("Press Q to finish and quit.\n")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Capture screenshot
                    screenshot_count += 1
                    filename = f"screenshot_{screenshot_count:02d}_{gui.active_tab.lower().replace(' ', '_')}.png"
                    capture_screenshot(gui.screen, filename)
                    print(f"Captured screenshot {screenshot_count}")
                elif event.key == pygame.K_t:
                    gui.start_tour()
                elif event.key == pygame.K_h:
                    gui.show_instructions = not gui.show_instructions
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if gui._handle_tour_click(event.pos):
                        continue
                    if gui._handle_tab_click(event.pos):
                        continue
                    gui._handle_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                gui._handle_hover(event.pos)
        
        gui._draw()
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print(f"\nScreenshot capture complete! {screenshot_count} screenshots saved to ./screenshots/")
    print("You can now add these to your README.md")

if __name__ == "__main__":
    main()
