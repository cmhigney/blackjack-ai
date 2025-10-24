# Blackjack Card Counting AI

A full-stack blackjack application that implements card counting to achieve positive expected value. Built to explore probability theory, algorithmic decision-making, and full-stack web development.

## Overview

This project simulates a professional blackjack player using the Hi-Lo card counting system, optimal basic strategy, and Wonging (selective play). The AI tracks deck composition, calculates true count, and adjusts betting strategy to gain an edge over the house.

## Game Interface
<img width="3397" height="1831" alt="image" src="https://github.com/user-attachments/assets/a18a607b-7b00-41bd-9ab4-35f36388fc0f" />


**Key Features:**
- Hi-Lo card counting system with true count conversion
- Optimal basic strategy for all playing decisions
- Wonging strategy (sitting out unfavorable counts)
- Dynamic bet sizing based on advantage (1-8x spread)
- Real-time web interface with casino-style visualization

## Quick Start

```bash
# Install dependencies
pip install flask

# Run the web application
python blackjackapp.py

# Open browser to http://localhost:5000
```

Click "NEW GAME" to initialize a session and watch the AI play.

## Development & AI Assistance

This project was developed to learn about probabilistic algorithms and full-stack development. The core game logic and mathematical implementations are original work, while AI assistance was used for frontend development as a learning tool.

### Independently Developed Components:
- **Card Counting Implementation** - Hi-Lo system with running/true count calculations
- **Basic Strategy Engine** - Decision matrix covering all player hand scenarios
- **Wonging Logic** - Threshold-based selective play algorithm
- **Bet Sizing Algorithm** - Kelly Criterion-inspired bet optimization
- **Game State Management** - Object-oriented architecture with 7 classes

### AI-Assisted Development (Claude AI):
- **Frontend Implementation** - HTML/CSS/JavaScript patterns for the web interface
- **CSS Animations** - Card dealing effects and transitions
- **Flask API Design** - RESTful endpoints and JSON serialization
- **Async JavaScript** - Proper async/await patterns for API communication

As someone still developing frontend skills, I used AI assistance to understand modern JavaScript patterns and CSS techniques. This allowed me to focus on the algorithmic challenges (the core learning objective) while still delivering a polished final product.

## How Card Counting Works

### The Hi-Lo System

Card counting exploits the fact that high cards (10, J, Q, K, A) favor the player while low cards (2-6) favor the dealer.

**Card Values:**
- Low cards (2-6): +1
- Neutral (7-9): 0  
- High cards (10-A): -1

**Running Count:** Sum of all card values seen
**True Count:** Running count ÷ Decks remaining

**Example:**
```
Running count: +12
Decks remaining: 3
True count: +4 (strong player advantage)
→ AI bets 6-8x minimum
```

### Wonging Strategy

Named after blackjack author Stanford Wong, "Wonging" means only playing when you have an edge. When the true count drops below -1, the AI sits out that hand but continues tracking cards. This improves win rate by avoiding negative expectation situations.

### Expected Results

Based on 1000+ hand simulations:
- **Hands sat out:** 30-40% (when count is unfavorable)
- **ROI:** 0.5-2% (positive expectation)
- **Volatility:** High short-term variance, positive long-term trend

This aligns with documented card counting performance in casino environments.

## Technical Implementation

### Backend (Python)
- **Language:** Python 3.13
- **Framework:** Flask 3.0
- **Architecture:** Object-oriented design with separation of concerns
- **Key Classes:** `Card`, `Deck`, `Hand`, `CardCounter`, `BankrollManager`, `BasicStrategy`, `BlackjackGame`

### Frontend  
- **Stack:** Vanilla HTML/CSS/JavaScript (no frameworks)
- **Styling:** Casino-themed UI with CSS animations
- **API Communication:** Fetch API with async/await
- **State Management:** Client-side game state updates

### Architecture
```
┌─────────────────┐
│  Web Interface  │ (HTML/CSS/JS)
│  (templates/)   │
└────────┬────────┘
         │ HTTP Requests
         ▼
┌─────────────────┐
│   Flask API     │ (blackjackapp.py)
│   RESTful       │
└────────┬────────┘
         │ Function Calls
         ▼
┌─────────────────┐
│  Game Engine    │ (blackjackai.py)
│  Card Counting  │
│  Basic Strategy │
└─────────────────┘
```

## Project Structure

```
blackjack_python/
├── blackjackai.py         # Core game engine and algorithms
├── blackjackapp.py        # Flask web server and API
└── templates/
    └── index.html         # Frontend interface
```

## Learning Outcomes

**Probability & Statistics:**
- Expected value calculations
- Variance and bankroll requirements
- Statistical advantage vs. house edge

**Algorithms:**
- State tracking across multiple game rounds
- Decision trees (basic strategy)
- Threshold-based betting strategies

**Software Engineering:**
- Object-oriented design principles
- API design and implementation
- Frontend-backend integration
- Using AI tools effectively in development

## Resources & References

### Blackjack & Card Counting Theory:
- **Blackjack Apprenticeship - Strategy Charts**: https://www.blackjackapprenticeship.com/blackjack-strategy-charts/
- **Texas A&M University - Basic Strategy Analysis (PDF)**: https://people.tamu.edu/~phoward/m442/strategy21.pdf
- **Blackjack Apprenticeship - How to Count Cards**: https://www.blackjackapprenticeship.com/how-to-count-cards/
- **Danny Booboo - Card Counting Tutorial**: https://dannybooboo.com/how-to-count-cards-the-easy-way/

### Development Resources:
- **Claude AI** - Frontend development assistance (HTML/CSS/JS patterns)
- **Stack Overflow** - Flask routing and JSON serialization
- **MDN Web Docs** - JavaScript async/await patterns
- **Flask Documentation** - API design patterns
- **GitHub repos** - Studied similar blackjack implementations for architecture ideas:
  - [PrintName/BlackjackCardCounter](https://github.com/PrintName/BlackjackCardCounter) 
  - [seblau/BlackJack-Simulator](https://github.com/seblau/BlackJack-Simulator)

### Testing & Validation:
- Verified basic strategy against published charts
- Validated counting system against known simulations
- Cross-referenced bet sizing with Kelly Criterion literature

## Limitations & Future Improvements

**Current Limitations:**
- Single-player only (no multi-hand or multi-player)
- One counting system (Hi-Lo only)
- No strategy deviations based on count
- Limited test coverage

**Potential Improvements:**
- Implement additional counting systems (KO, Hi-Opt II, Omega II)
- Add the Illustrious 18 strategy deviations
- Build comprehensive test suite
- Add database for long-term statistics
- Implement multi-hand play
- Create data visualizations (bankroll over time, count distribution)

## Performance Notes

**Mathematical Edge:**
- Basic strategy alone: ~0.5% house edge
- Perfect counting with bet spread: ~1% player edge  
- With Wonging: ~1.5% player edge

**Important:** This advantage only materializes over thousands of hands. Short-term results will show high variance. Professional card counters require substantial bankrolls to weather losing streaks.

## Current Issue
- The dealer's hand seems to not show when the AI player is sitting out (not betting). Working on a fix so the user can see the dealer's cards every hand.

## Legal & Ethical Considerations

**Educational Purpose:** This project was created for learning probability theory and algorithm design.

**Legality:** Card counting is legal in most jurisdictions, but casinos reserve the right to refuse service to anyone. Most professional counters are eventually banned.

**Disclaimer:** This is a simulation for educational purposes. Real gambling involves significant financial risk. The mathematical edge only works with perfect play and substantial bankroll. Don't gamble money you can't afford to lose.

## License

MIT License - Free to use, modify, and distribute

## Contact

Cameron Higney  
Email: cmhigney@uri.edu, cmhigney@gmail.com  
University of Rhode Island - Computer Science
