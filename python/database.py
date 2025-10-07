#!/usr/bin/env python3
"""
Database module for storing and analyzing blackjack game data
"""

import sqlite3
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='database/blackjack_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hands table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                formkey TEXT DEFAULT 'default',
                wager_amount INTEGER,
                wager_currency TEXT,
                player_cards TEXT,
                dealer_cards TEXT,
                player_value INTEGER,
                dealer_value INTEGER,
                player_split_cards TEXT,
                player_split_value INTEGER,
                has_split BOOLEAN,
                doubled_down BOOLEAN,
                bought_insurance BOOLEAN,
                status TEXT,
                status_split TEXT,
                payout INTEGER,
                coins_before INTEGER,
                coins_after INTEGER,
                marseybux_before INTEGER,
                marseybux_after INTEGER,
                raw_state TEXT
            )
        ''')
        
        # Actions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hand_id INTEGER,
                action TEXT,
                player_value INTEGER,
                dealer_value INTEGER,
                timestamp TEXT,
                FOREIGN KEY (hand_id) REFERENCES hands (id)
            )
        ''')
        
        # Statistics table for quick lookups
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                total_hands INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                pushes INTEGER DEFAULT 0,
                blackjacks INTEGER DEFAULT 0,
                busts INTEGER DEFAULT 0,
                total_wagered INTEGER DEFAULT 0,
                total_won INTEGER DEFAULT 0,
                total_lost INTEGER DEFAULT 0
            )
        ''')
        
        # Dealer patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dealer_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upcard TEXT,
                final_value INTEGER,
                busted BOOLEAN,
                count INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def store_hand(self, state, gambler, timestamp, formkey='default'):
        """Store a hand in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            wager = state.get('wager', {})
            
            cursor.execute('''
                INSERT INTO hands (
                    timestamp, formkey, wager_amount, wager_currency,
                    player_cards, dealer_cards, player_value, dealer_value,
                    player_split_cards, player_split_value,
                    has_split, doubled_down, bought_insurance,
                    status, status_split, payout,
                    coins_before, marseybux_before,
                    raw_state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                formkey,
                wager.get('amount', 0),
                wager.get('currency', 'coins'),
                json.dumps(state.get('player', [])),
                json.dumps(state.get('dealer', [])),
                state.get('player_value', 0),
                state.get('dealer_value', 0),
                json.dumps(state.get('player_split', [])),
                state.get('player_split_value', 0),
                state.get('has_player_split', False),
                state.get('player_doubled_down', False),
                state.get('player_bought_insurance', False),
                state.get('status', ''),
                state.get('status_split', ''),
                state.get('payout', 0),
                gambler.get('coins', 0),
                gambler.get('marseybux', 0),
                json.dumps(state)
            ))
            
            hand_id = cursor.lastrowid
            conn.commit()
            
            return hand_id
        
        except Exception as e:
            logger.error(f"Error storing hand: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def store_action(self, hand_id, action, player_value, dealer_value):
        """Store an action taken during a hand"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO actions (hand_id, action, player_value, dealer_value, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (hand_id, action, player_value, dealer_value, datetime.now().isoformat()))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error storing action: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def update_hand_outcome(self, hand_id, state):
        """Update hand with final outcome"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE hands 
                SET status = ?, status_split = ?, payout = ?,
                    dealer_cards = ?, dealer_value = ?,
                    player_value = ?, player_split_value = ?
                WHERE id = ?
            ''', (
                state.get('status'),
                state.get('status_split'),
                state.get('payout', 0),
                json.dumps(state.get('dealer', [])),
                state.get('dealer_value', 0),
                state.get('player_value', 0),
                state.get('player_split_value', 0),
                hand_id
            ))
            
            # Update dealer patterns
            if state.get('dealer_value') and len(state.get('dealer', [])) > 0:
                upcard = state.get('dealer', [])[0]
                dealer_value = state.get('dealer_value', 0)
                busted = dealer_value < 0 or dealer_value > 21
                
                cursor.execute('''
                    INSERT INTO dealer_patterns (upcard, final_value, busted, count)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT DO UPDATE SET count = count + 1
                ''')
            
            # Update daily statistics
            self._update_statistics(cursor, state)
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating hand outcome: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _update_statistics(self, cursor, state):
        """Update statistics table"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get or create today's stats
        cursor.execute('SELECT id FROM statistics WHERE date = ?', (today,))
        result = cursor.fetchone()
        
        if not result:
            cursor.execute('''
                INSERT INTO statistics (date) VALUES (?)
            ''', (today,))
        
        # Update based on outcome
        status = state.get('status', '')
        wager = state.get('wager', {}).get('amount', 0)
        payout = state.get('payout', 0)
        
        if status == 'BLACKJACK':
            cursor.execute('''
                UPDATE statistics 
                SET blackjacks = blackjacks + 1,
                    wins = wins + 1,
                    total_hands = total_hands + 1,
                    total_wagered = total_wagered + ?,
                    total_won = total_won + ?
                WHERE date = ?
            ''', (wager, payout - wager, today))
        elif status == 'WON':
            cursor.execute('''
                UPDATE statistics 
                SET wins = wins + 1,
                    total_hands = total_hands + 1,
                    total_wagered = total_wagered + ?,
                    total_won = total_won + ?
                WHERE date = ?
            ''', (wager, payout - wager, today))
        elif status == 'LOST':
            player_value = state.get('player_value', 0)
            if player_value < 0 or player_value > 21:
                cursor.execute('''
                    UPDATE statistics 
                    SET losses = losses + 1,
                        busts = busts + 1,
                        total_hands = total_hands + 1,
                        total_wagered = total_wagered + ?,
                        total_lost = total_lost + ?
                    WHERE date = ?
                ''', (wager, wager, today))
            else:
                cursor.execute('''
                    UPDATE statistics 
                    SET losses = losses + 1,
                        total_hands = total_hands + 1,
                        total_wagered = total_wagered + ?,
                        total_lost = total_lost + ?
                    WHERE date = ?
                ''', (wager, wager, today))
        elif status == 'PUSHED':
            cursor.execute('''
                UPDATE statistics 
                SET pushes = pushes + 1,
                    total_hands = total_hands + 1,
                    total_wagered = total_wagered + ?
                WHERE date = ?
            ''', (wager, today))
    
    def get_statistics(self, formkey=None):
        """Get current statistics, optionally filtered by formkey"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get statistics from hands table (allows formkey filtering)
            if formkey:
                query = '''
                    SELECT 
                        COUNT(*) as total_hands,
                        SUM(CASE WHEN status = 'WON' OR status = 'BLACKJACK' THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN status = 'LOST' THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN status = 'PUSHED' THEN 1 ELSE 0 END) as pushes,
                        SUM(CASE WHEN status = 'BLACKJACK' THEN 1 ELSE 0 END) as blackjacks,
                        SUM(CASE WHEN (player_value < 0 OR player_value > 21) AND status = 'LOST' THEN 1 ELSE 0 END) as busts,
                        SUM(wager_amount) as total_wagered,
                        SUM(CASE WHEN status = 'WON' OR status = 'BLACKJACK' THEN payout - wager_amount ELSE 0 END) as total_won,
                        SUM(CASE WHEN status = 'LOST' THEN wager_amount ELSE 0 END) as total_lost
                    FROM hands
                    WHERE status IN ('WON', 'LOST', 'PUSHED', 'BLACKJACK')
                      AND formkey = ?
                '''
                cursor.execute(query, (formkey,))
            else:
                query = '''
                    SELECT 
                        COUNT(*) as total_hands,
                        SUM(CASE WHEN status = 'WON' OR status = 'BLACKJACK' THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN status = 'LOST' THEN 1 ELSE 0 END) as losses,
                        SUM(CASE WHEN status = 'PUSHED' THEN 1 ELSE 0 END) as pushes,
                        SUM(CASE WHEN status = 'BLACKJACK' THEN 1 ELSE 0 END) as blackjacks,
                        SUM(CASE WHEN (player_value < 0 OR player_value > 21) AND status = 'LOST' THEN 1 ELSE 0 END) as busts,
                        SUM(wager_amount) as total_wagered,
                        SUM(CASE WHEN status = 'WON' OR status = 'BLACKJACK' THEN payout - wager_amount ELSE 0 END) as total_won,
                        SUM(CASE WHEN status = 'LOST' THEN wager_amount ELSE 0 END) as total_lost
                    FROM hands
                    WHERE status IN ('WON', 'LOST', 'PUSHED', 'BLACKJACK')
                '''
                cursor.execute(query)
            
            result = cursor.fetchone()
            
            if result and result[0]:
                total_hands = result[0] or 0
                wins = result[1] or 0
                losses = result[2] or 0
                pushes = result[3] or 0
                blackjacks = result[4] or 0
                busts = result[5] or 0
                total_wagered = result[6] or 0
                total_won = result[7] or 0
                total_lost = result[8] or 0
                
                win_rate = (wins / total_hands * 100) if total_hands > 0 else 0
                loss_rate = (losses / total_hands * 100) if total_hands > 0 else 0
                push_rate = (pushes / total_hands * 100) if total_hands > 0 else 0
                blackjack_rate = (blackjacks / total_hands * 100) if total_hands > 0 else 0
                bust_rate = (busts / total_hands * 100) if total_hands > 0 else 0
                
                net_profit = total_won - total_lost
                roi = (net_profit / total_wagered * 100) if total_wagered > 0 else 0
                
                return {
                    'total_hands': total_hands,
                    'wins': wins,
                    'losses': losses,
                    'pushes': pushes,
                    'blackjacks': blackjacks,
                    'busts': busts,
                    'win_rate': round(win_rate, 2),
                    'loss_rate': round(loss_rate, 2),
                    'push_rate': round(push_rate, 2),
                    'blackjack_rate': round(blackjack_rate, 2),
                    'bust_rate': round(bust_rate, 2),
                    'total_wagered': total_wagered,
                    'total_won': total_won,
                    'total_lost': total_lost,
                    'net_profit': net_profit,
                    'roi': round(roi, 2)
                }
            else:
                return {
                    'total_hands': 0,
                    'wins': 0,
                    'losses': 0,
                    'pushes': 0,
                    'blackjacks': 0,
                    'busts': 0,
                    'win_rate': 0,
                    'loss_rate': 0,
                    'push_rate': 0,
                    'blackjack_rate': 0,
                    'bust_rate': 0,
                    'total_wagered': 0,
                    'total_won': 0,
                    'total_lost': 0,
                    'net_profit': 0,
                    'roi': 0
                }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
        finally:
            conn.close()
    
    def get_dealer_patterns(self):
        """Get dealer patterns analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT upcard, 
                       SUM(CASE WHEN busted = 1 THEN count ELSE 0 END) as bust_count,
                       SUM(count) as total_count
                FROM dealer_patterns
                GROUP BY upcard
            ''')
            
            patterns = {}
            for row in cursor.fetchall():
                upcard, bust_count, total_count = row
                bust_rate = (bust_count / total_count * 100) if total_count > 0 else 0
                patterns[upcard] = {
                    'total': total_count,
                    'busts': bust_count,
                    'bust_rate': round(bust_rate, 2)
                }
            
            return patterns
        
        except Exception as e:
            logger.error(f"Error getting dealer patterns: {e}")
            return {}
        finally:
            conn.close()