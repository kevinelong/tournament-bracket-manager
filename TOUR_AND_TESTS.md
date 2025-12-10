# User Tour System & Test Suite

## Interactive User Tour

The Tournament Manager now includes a comprehensive interactive tour that guides new users through all features.

### Starting the Tour

- **Press `T`** at any time to start/restart the tour
- **Press `ESC`** to exit the tour
- The tour automatically activates on first launch (planned feature)

### Tour Features

#### Visual Highlights
- **Pulsing borders** around featured UI elements
- **Semi-transparent overlay** dims non-highlighted areas
- **Animated pulses** draw attention to important controls
- **Automatic tab switching** navigates to relevant sections

#### Navigation Controls
- **Next Button**: Advance to the next tour step
- **Previous Button**: Go back to review previous steps
- **Skip Tour**: Exit the tour at any time
- **Finish Button**: Appears on the last step

#### Tour Steps (13 Total)

1. **Welcome** - Introduction to the tour system
2. **Creating Tournaments** - How to create new tournaments
3. **Tournament List** - Viewing and selecting tournaments
4. **Editable Fields** - Editing tournament details (name, location, dates)
5. **Managing Players** - Adding and removing players
6. **Generate Bracket** - Creating tournament brackets
7. **View Bracket** - Understanding the bracket display
8. **Match Interaction** - Selecting matches and declaring winners
9. **Final Results** - Viewing tournament standings
10. **Dangerous Operations** - Reset and reshuffle features
11. **Auto-Save** - Explaining persistence
12. **Keyboard Shortcuts** - H for help, T for tour, ESC for cancel
13. **Tour Complete** - Completion message

### Tour Implementation

The tour system includes:
- `TourStep` dataclass for defining each step
- Automatic highlight rectangle calculations
- Click-through support for interactive demonstrations
- Action requirement tracking (optional vs required actions)
- Tab synchronization

## Comprehensive Test Suite

The project includes 38 automated tests ensuring all features work correctly.

### Running Tests

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run all tests
python test_tournament.py
```

### Test Coverage

#### TestMatch (4 tests)
- ✅ Match creation
- ✅ Setting valid winners
- ✅ Invalid winner handling
- ✅ Match completion status

#### TestTournamentMetadata (3 tests)
- ✅ Metadata creation
- ✅ Dictionary serialization
- ✅ Dictionary deserialization

#### TestTournamentBracket (7 tests)
- ✅ Bracket with power-of-2 participants
- ✅ Bracket with byes (non-power-of-2)
- ✅ Winner advancement through rounds
- ✅ Champion determination
- ✅ Champion with no winner
- ✅ Bracket state reset
- ✅ Bracket serialization/deserialization
- ✅ Empty bracket handling

#### TestTourSystem (8 tests)
- ✅ Tour step creation
- ✅ GUI tour initialization
- ✅ Starting the tour
- ✅ Advancing to next step
- ✅ Going to previous step
- ✅ Boundary conditions (first/last step)
- ✅ Ending the tour
- ✅ Tour completion at last step
- ✅ All tour steps validation

#### TestGUIFeatures (13 tests)
- ✅ Creating tournaments
- ✅ Loading tournaments
- ✅ Editing tournament fields
- ✅ Adding players
- ✅ Removing players
- ✅ Generating brackets
- ✅ Resetting tournaments
- ✅ Reshuffling tournaments
- ✅ Auto-save functionality
- ✅ Tab switching
- ✅ UI scaling calculations

#### TestEdgeCases (3 tests)
- ✅ Single player bracket
- ✅ Large bracket (64 players)
- ✅ Bye match handling

### Test Results

```
Ran 38 tests in ~6 seconds

OK
Success rate: 100.0%
```

### Test Features

- **Isolated test environments** using temp directories
- **Pygame headless mode** for CI/CD compatibility
- **Comprehensive coverage** of all tour-documented features
- **Edge case validation** for robustness
- **Serialization tests** for data persistence
- **GUI interaction tests** for user workflows

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `T` | Start/restart user tour |
| `H` | Toggle help instructions (Bracket tab) |
| `ESC` | Cancel editing / Close dialogs / Exit tour |
| `Enter` | Save text input / Add player |
| `Backspace` | Delete character in text input |

## Feature Verification

All features documented in the tour have corresponding tests:

✅ **Create Tournament** - `test_create_tournament`
✅ **Load Tournament** - `test_load_tournament`
✅ **Edit Tournament Fields** - `test_edit_tournament_fields`
✅ **Add Players** - `test_add_players`
✅ **Remove Players** - `test_remove_players`
✅ **Generate Bracket** - `test_generate_bracket`
✅ **Match Selection** - `test_select_winner_advances`
✅ **Reset Tournament** - `test_reset_tournament`
✅ **Reshuffle Tournament** - `test_reshuffle_tournament`
✅ **Auto-Save** - `test_auto_save`
✅ **Tab Switching** - `test_tab_switching`
✅ **UI Scaling** - `test_scaling_calculation`

## Development Guidelines

### Adding New Features

1. **Create the feature** in `tournament.py`
2. **Add a tour step** in `_initialize_tour_steps()`
3. **Write tests** in `test_tournament.py`
4. **Run tests** to verify (should maintain 100% pass rate)
5. **Update this document** with new feature details

### Tour Step Template

```python
TourStep(
    id="feature_id",
    title="Feature Title",
    description="Detailed description of what the feature does.",
    tab="TabName",  # Which tab to show
    highlight_rect=(x, y, width, height),  # Optional highlight area
    action_required="What the user should do"  # Optional
)
```

### Test Template

```python
def test_new_feature(self):
    """Test description."""
    # Setup
    gui = TournamentBracketGUI(width=800, height=600)
    
    # Action
    # ... perform action ...
    
    # Assert
    self.assertEqual(expected, actual)
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- Uses headless pygame driver (`SDL_VIDEODRIVER=dummy`)
- Creates isolated temporary directories
- Cleans up after each test
- Returns exit code 0 on success, 1 on failure

## Future Enhancements

Potential improvements for the tour system:

- [ ] Auto-start tour for first-time users
- [ ] Progress tracking (remember which steps completed)
- [ ] Multiple tour modes (beginner, advanced, specific features)
- [ ] Video/animation support in tour steps
- [ ] Tooltips for all interactive elements
- [ ] Accessibility features (screen reader support)
- [ ] Tour analytics (which steps users skip)

## Troubleshooting

### Tests Fail
- Ensure pygame is installed: `pip install pygame`
- Verify Python version: 3.12+ recommended
- Check virtual environment is activated

### Tour Not Showing
- Press `T` to manually start tour
- Check `tour_active` state in debugger
- Verify `tour_steps` list is populated

### Highlights Misaligned
- Tour step highlight rectangles may need adjustment
- UI scaling can affect positions
- Update highlight_rect coordinates as needed
