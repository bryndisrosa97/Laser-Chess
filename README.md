# Laser Chess against AI

## Introduction
Laser Chess is a dynamic two-player strategy game. The primary objective is to target the opponent’s queen with a laser while safeguarding your own. A hit on a queen concludes the game, crowning the player with the intact queen as the victor.

![image](https://github.com/bryndisrosa97/Laser-Chess/assets/61384036/2388e65e-b6cf-48b7-b607-b57a6d14bccf)

## Game Setup
- Players begin by selecting their token color.
- The board is initialized as per Ace [1], with the blue token player initiating the game.
- Each player is equipped with 13 tokens:
  - **1 Queen**
  - **1 Laser**
  - **2 Switches**
  - **2 Defenders**
  - **7 Deflectors**

## Token Roles
- **Laser**: Positioned in a fixed corner, it emits a laser beam at the end of its player's turn. Tokens hit by the laser, which don't reflect it, are removed. The laser is invulnerable.
- **Queen**: The primary piece to protect. All tokens, barring the laser, serve to defend the queen.
- **Deflectors**: Features three sides - two non-mirrored and one mirrored. The mirrored side reflects the laser beam at a 90-degree angle.
- **Defender**: Has four sides with three non-mirrored and one mirrored. The mirrored side sends the laser beam directly back.
- **Switch**: Equipped with two mirrored sides, reflecting the laser beam at 90 degrees. It's impervious to the laser.

## Gameplay
1. Players alternate turns.
2. On their turn, a player can:
   - Rotate a token by 90 degrees (excluding the laser).
   - Move a token in any direction to an unoccupied tile (excluding the laser).
3. The turn concludes with the laser's activation.
4. The queen, given its symmetrical design, cannot be rotated to bypass a turn.

## Board Specifications
- Some tiles are color-coded as red or blue. Only matching colored tokens can occupy these tiles.

## Modifications from Official Rules
- The official game features a king, which we've replaced with a queen.
- We've omitted the switch's ability to swap places with adjacent deflectors or defenders.
- The three-time board repetition stalemate rule has been excluded.
- Our version introduces a rule preventing the rotation of the queen to skip turns.

