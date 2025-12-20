#!/usr/bin/env python3
"""
New conversational format pipeline for Alif fine-tuning
"""
import json
import random
import os
from config import Config
from generator import ConversationGenerator
from utils import validate_conversation_turn, convert_to_messages_format, create_signature
import logging

def main():
    print(f"🚀 Starting Alif Conversational Pipeline | Target: {Config.TARGET_ROWS} rows")
    
    # 1. Load existing rows to avoid duplicates
    existing_signatures = set()
    current_rows = 0
    
    if os.path.exists(Config.OUTPUT_FILE):
        with open(Config.OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # Create signature from messages
                    user_msg = data['messages'][0]['content']
                    assistant_msg = data['messages'][1]['content']
                    signature = f"{user_msg[:50]}|{assistant_msg[:30]}"
                    existing_signatures.add(signature)
                    current_rows += 1
                except:
                    continue
        print(f"🔄 Resuming from {current_rows} existing rows...")
    
    # 2. Setup scenario queue
    scenario_queue = Config.SCENARIOS.copy()
    random.shuffle(scenario_queue)
    
    failed_attempts = 0
    max_failed_attempts = 10
    
    print(f"📊 Progress: {current_rows}/{Config.TARGET_ROWS}")
    
    while current_rows < Config.TARGET_ROWS and failed_attempts < max_failed_attempts:
        try:
            # Refresh scenario queue when needed
            if len(scenario_queue) < Config.BATCH_SIZE:
                scenario_queue = Config.SCENARIOS.copy()
                random.shuffle(scenario_queue)

            # Select scenarios for this batch
            batch_scenarios = []
            for _ in range(min(Config.BATCH_SIZE, len(scenario_queue))):
                batch_scenarios.append(scenario_queue.pop())
            
            print(f"🔄 Generating batch with {len(batch_scenarios)} scenarios...")
            
            try:
                conversation_turns = ConversationGenerator.fetch_batch(batch_scenarios)
                print(f"✅ Generated {len(conversation_turns)} conversation turns")
                failed_attempts = 0  # Reset on success
            except Exception as e:
                failed_attempts += 1
                logging.error(f"Batch failed (attempt {failed_attempts}): {e}")
                print(f"❌ Batch failed: {e}")
                continue 

            new_rows_to_save = []
            valid_turns = 0
            
            for turn in conversation_turns:
                if validate_conversation_turn(turn):
                    valid_turns += 1
                    
                    # Check for duplicates
                    signature = create_signature(turn)
                    
                    if signature not in existing_signatures:
                        # Convert to messages format
                        training_row = convert_to_messages_format(turn)
                        new_rows_to_save.append(training_row)
                        existing_signatures.add(signature)
            
            print(f"📊 Valid turns: {valid_turns}/{len(conversation_turns)}, New rows: {len(new_rows_to_save)}")
            
            # Check if we need to limit rows to reach exact target
            rows_needed = Config.TARGET_ROWS - current_rows
            if len(new_rows_to_save) > rows_needed:
                new_rows_to_save = new_rows_to_save[:rows_needed]
                print(f"🎯 Limited to {len(new_rows_to_save)} rows to reach target")

            # Save new rows
            if new_rows_to_save:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(Config.OUTPUT_FILE), exist_ok=True)
                
                with open(Config.OUTPUT_FILE, 'a', encoding='utf-8') as f:
                    for row in new_rows_to_save:
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                
                current_rows += len(new_rows_to_save)
                print(f"💾 Saved {len(new_rows_to_save)} rows. Total: {current_rows}/{Config.TARGET_ROWS}")
            
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user.")
            break
        except Exception as e:
            logging.critical(f"Critical Error: {e}")
            print(f"💥 Critical error: {e}")
            break

    print(f"\n✅ Pipeline completed! Dataset saved to {Config.OUTPUT_FILE}")
    print(f"📊 Final count: {current_rows} conversation turns")
    
    if current_rows >= Config.TARGET_ROWS:
        print("🎯 Target reached successfully!")
    else:
        print(f"⚠️  Stopped at {current_rows}/{Config.TARGET_ROWS} rows")

if __name__ == "__main__":
    main()