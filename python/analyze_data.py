#!/usr/bin/env python3
"""
Data analysis script for blackjack statistics
Provides detailed analysis of collected game data
"""

import sqlite3
import json
from datetime import datetime
import argparse
from tabulate import tabulate

class BlackjackAnalyzer:
    def __init__(self, db_path='database/blackjack_data.db'):
        self.db_path = db_path
    
    def analyze(self):
        """Run comprehensive analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print(" BLACKJACK DATA ANALYSIS")
        print("="*60)
        
        # Overall statistics
        self._print_overall_stats(cursor)
        
        # Win/Loss breakdown
        self._print_outcome_breakdown(cursor)
        
        # Dealer patterns
        self._print_dealer_patterns(cursor)
        
        # Strategy effectiveness
        self._print_strategy_effectiveness(cursor)
        
        # Time-based analysis
        self._print_time_analysis(cursor)
        
        conn.close()
    
    def _print_overall_stats(self, cursor):
        """Print overall statistics"""
        cursor.execute('''
            SELECT COUNT(*) as total_hands,
                   SUM(CASE WHEN status = 'WON' OR status = 'BLACKJACK' THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN status = 'LOST' THEN 1 ELSE 0 END) as losses,
                   SUM(CASE WHEN status = 'PUSHED' THEN 1 ELSE 0 END) as pushes,
                   SUM(CASE WHEN status = 'BLACKJACK' THEN 1 ELSE 0 END) as blackjacks,
                   SUM(wager_amount) as total_wagered,
                   SUM(payout) as total_payout
            FROM hands
            WHERE status IN ('WON', 'LOST', 'PUSHED', 'BLACKJACK')
        ''')
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            total, wins, losses, pushes, blackjacks, wagered, payout = result
            win_rate = (wins / total * 100) if total > 0 else 0
            house_edge = ((wagered - payout) / wagered * 100) if wagered > 0 else 0
            
            print("\n### OVERALL STATISTICS ###")
            data = [
                ['Total Hands', total],
                ['Wins', f"{wins} ({win_rate:.1f}%)"],
                ['Losses', f"{losses} ({losses/total*100:.1f}%)"],
                ['Pushes', f"{pushes} ({pushes/total*100:.1f}%)"],
                ['Blackjacks', f"{blackjacks} ({blackjacks/total*100:.1f}%)"],
                ['Total Wagered', wagered],
                ['Total Payout', payout],
                ['Net Result', payout - wagered],
                ['House Edge', f"{house_edge:.2f}%"]
            ]
            print(tabulate(data, headers=['Metric', 'Value'], tablefmt='grid'))
    
    def _print_outcome_breakdown(self, cursor):
        """Print detailed outcome breakdown"""
        print("\n### OUTCOME BREAKDOWN ###")
        
        # By player hand value
        cursor.execute('''
            SELECT player_value, 
                   COUNT(*) as hands,
                   SUM(CASE WHEN status = 'WON' OR status = 'BLACKJACK' THEN 1 ELSE 0 END) as wins
            FROM hands
            WHERE status IN ('WON', 'LOST', 'PUSHED', 'BLACKJACK')
                  AND player_value > 0
            GROUP BY player_value
            ORDER BY player_value
        ''')
        
        data = []
        for row in cursor.fetchall():
            value, hands, wins = row
            win_rate = (wins / hands * 100) if hands > 0 else 0
            data.append([value, hands, wins, f"{win_rate:.1f}%"])
        
        if data:
            print("\nBy Player Hand Value:")
            print(tabulate(data, headers=['Value', 'Hands', 'Wins', 'Win Rate'], tablefmt='grid'))
    
    def _print_dealer_patterns(self, cursor):
        """Print dealer pattern analysis"""
        print("\n### DEALER PATTERNS ###")
        
        # Dealer bust rates by upcard
        cursor.execute('''
            SELECT 
                SUBSTR(dealer_cards, 3, 2) as upcard,
                COUNT(*) as hands,
                SUM(CASE WHEN dealer_value < 0 OR dealer_value > 21 THEN 1 ELSE 0 END) as busts
            FROM hands
            WHERE status IN ('WON', 'LOST', 'PUSHED', 'BLACKJACK')
                  AND dealer_cards != '["?"]'
            GROUP BY upcard
            ORDER BY upcard
        ''')
        
        data = []
        for row in cursor.fetchall():
            upcard, hands, busts = row
            if upcard and hands > 0:
                bust_rate = (busts / hands * 100)
                data.append([upcard.strip('"], '), hands, busts, f"{bust_rate:.1f}%"])
        
        if data:
            print("\nDealer Bust Rates by Upcard:")
            print(tabulate(data, headers=['Upcard', 'Hands', 'Busts', 'Bust Rate'], tablefmt='grid'))
        
        # Expected vs actual dealer values
        cursor.execute('''
            SELECT 
                SUBSTR(dealer_cards, 3, 2) as upcard,
                AVG(CASE WHEN dealer_value > 0 AND dealer_value <= 21 THEN dealer_value ELSE 0 END) as avg_value,
                COUNT(*) as hands
            FROM hands
            WHERE status IN ('WON', 'LOST', 'PUSHED', 'BLACKJACK')
                  AND dealer_value > 0 AND dealer_value <= 21
            GROUP BY upcard
            HAVING hands > 10
            ORDER BY upcard
        ''')
        
        data = []
        for row in cursor.fetchall():
            upcard, avg_value, hands = row
            if upcard:
                data.append([upcard.strip('"], '), f"{avg_value:.1f}", hands])
        
        if data:
            print("\nAverage Dealer Final Value by Upcard:")
            print(tabulate(data, headers=['Upcard', 'Avg Value', 'Sample Size'], tablefmt='grid'))
    
    def _print_strategy_effectiveness(self, cursor):
        """Print strategy effectiveness analysis"""
        print("\n### STRATEGY EFFECTIVENESS ###")
        
        # Double down success rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total_doubles,
                SUM(CASE WHEN status = 'WON' OR status = 'BLACKJACK' THEN 1 ELSE 0 END) as wins
            FROM hands
            WHERE doubled_down = 1
        ''')
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            doubles, wins = result
            success_rate = (wins / doubles * 100)
            print(f"\nDouble Down Success Rate: {wins}/{doubles} ({success_rate:.1f}%)")
        
        # Split success rate
        cursor.execute('''
            SELECT 
                COUNT(*) as total_splits,
                SUM(CASE WHEN status = 'WON' AND status_split = 'WON' THEN 1 
                         WHEN status = 'WON' OR status_split = 'WON' THEN 0.5
                         ELSE 0 END) as net_wins
            FROM hands
            WHERE has_split = 1
        ''')
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            splits, net_wins = result
            success_rate = (net_wins / splits * 100)
            print(f"Split Success Rate: {net_wins:.1f}/{splits} ({success_rate:.1f}%)")
        
        # Action distribution
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM actions
            GROUP BY action
            ORDER BY count DESC
        ''')
        
        data = []
        total_actions = 0
        for row in cursor.fetchall():
            action, count = row
            data.append([action, count])
            total_actions += count
        
        if data:
            print("\nAction Distribution:")
            for row in data:
                row.append(f"{row[1]/total_actions*100:.1f}%")
            print(tabulate(data, headers=['Action', 'Count', 'Percentage'], tablefmt='grid'))
    
    def _print_time_analysis(self, cursor):
        """Print time-based analysis"""
        print("\n### TIME-BASED ANALYSIS ###")
        
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as hands,
                SUM(CASE WHEN status = 'WON' OR status = 'BLACKJACK' THEN 1 ELSE 0 END) as wins,
                SUM(wager_amount) as wagered,
                SUM(payout) - SUM(wager_amount) as net_result
            FROM hands
            WHERE status IN ('WON', 'LOST', 'PUSHED', 'BLACKJACK')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 10
        ''')
        
        data = []
        for row in cursor.fetchall():
            date, hands, wins, wagered, net = row
            if hands > 0:
                win_rate = (wins / hands * 100)
                data.append([date, hands, f"{win_rate:.1f}%", wagered, net])
        
        if data:
            print("\nRecent Session Results:")
            print(tabulate(data, headers=['Date', 'Hands', 'Win Rate', 'Wagered', 'Net'], tablefmt='grid'))
    
    def export_to_csv(self, output_file='blackjack_analysis.csv'):
        """Export raw data to CSV for further analysis"""
        import csv
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM hands
            WHERE status IN ('WON', 'LOST', 'PUSHED', 'BLACKJACK')
        ''')
        
        with open(output_file, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write headers
            headers = [description[0] for description in cursor.description]
            csv_writer.writerow(headers)
            
            # Write data
            csv_writer.writerows(cursor.fetchall())
        
        conn.close()
        print(f"\nData exported to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze blackjack game data')
    parser.add_argument('--db', default='database/blackjack_data.db', help='Database file path')
    parser.add_argument('--export', action='store_true', help='Export data to CSV')
    
    args = parser.parse_args()
    
    analyzer = BlackjackAnalyzer(args.db)
    analyzer.analyze()
    
    if args.export:
        analyzer.export_to_csv()

if __name__ == '__main__':
    # Install tabulate if not present
    try:
        import tabulate
    except ImportError:
        print("Installing required package: tabulate")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
        import tabulate
    
    main()