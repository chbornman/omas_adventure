# Oma's Adventure
A charming 2D platformer game where you help Oma's three beloved pets reach her cozy bed!

## 🎮 About This Game

Help Shoogie, Florence, and Sue (Oma's three adorable pets) navigate through increasingly challenging rounds to reach Oma's bed safely. Each character has unique abilities and a precious 3 lives to complete their journey.

### ✨ Game Features
- **Three Unique Characters**: Shoogie (cat), Florence (cat), and Sue (dog) - each with special abilities
- **Lives System**: Each character has 3 hearts - lose them all and they're out of the adventure!
- **High Score System**: Compete for the top 10 spots with persistent leaderboards and player names
- **Beautiful Screens**: Animated title screen, game over sequences, and peaceful bedtime celebrations
- **Progressive Difficulty**: Each round brings more enemies and longer levels
- **Score Persistence**: Keep your earned points across rounds - only lose progress when all characters are defeated

### 🎯 How to Play
- **Movement**: ← → Arrow keys
- **Jump**: ↑ Arrow key (Sue can double jump!)
- **Attack**: SPACE (each character has unique attacks)
- **Switch Characters**: X key (when multiple characters are available)

## 🚀 Quick Start

### Using Docker (Recommended)
```bash
git clone https://github.com/chbornman/omas_adventure.git
cd omas_adventure
docker compose up -d
```

Visit `http://localhost:1213` and start playing!

### Local Development
```bash
git clone https://github.com/chbornman/omas_adventure.git
cd omas_adventure
pip install -r requirements.txt
python main.py
```

## 🏗️ Tech Stack
- **Python 3.11+** - Core game logic
- **Pygame 2.6+** - Game engine and graphics
- **Docker** - Containerized deployment
- **pygbag** - Web deployment via WebAssembly

## 🎨 Game Mechanics

### Character Abilities
- **Shoogie**: Meow wave attacks, gains omnidirectional attack charges
- **Florence**: Hairball projectiles, speed/jump boosts from plants
- **Sue**: Poo attacks, double jump, treat collection bonuses

### Scoring System
- **Enemy Defeat**: 50 points
- **Treat Collection**: 10 points  
- **Plant Pickup**: 20 points
- **Character Rescue**: 100 points
- **Round Completion**: 1000 points
- **Death Penalty**: -200 points (current round only)

## 📦 Docker Deployment

The game is fully containerized for easy deployment:

```yaml
# docker-compose.yml
services:
  omas-game2:
    build: .
    ports:
      - "1213:8080"
    volumes:
      - high_scores_data:/app/data
```

High scores persist between container restarts thanks to Docker volumes.

## 🙏 Credits

This game was built upon the excellent foundation provided by [JMWhitworth's Pygame Dungeon Game](https://github.com/JMWhitworth/Pygame-Dungeon-Game). We're grateful for the solid template that made this adventure possible!

### Additional Assets
- Character sprites: Custom created
- Sound effects: From the original template
- Game assets: Various sources

## 🔄 Development

To update the game while preserving high scores:
```bash
# Make your changes, then:
docker compose build
docker compose up -d
```

For a completely fresh start:
```bash
docker compose down --volumes
docker compose build --no-cache
docker compose up -d
```

## 🤝 Contributing

Feel free to contribute! This project welcomes:
- Bug fixes
- New character abilities
- Visual improvements  
- Performance optimizations
- Additional game features

## 📝 License

This project maintains the same license as the original template. Please see the LICENSE file for details.
