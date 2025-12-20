#!/usr/bin/env python3
"""
Quality analysis for conversational dataset
"""
import json
import re
from collections import Counter
from config import Config

def analyze_conversational_quality():
    """Analyze the quality of conversational dataset"""
    print("🔍 Analyzing Conversational Dataset Quality...")
    
    try:
        with open(Config.OUTPUT_FILE, 'r', encoding='utf-8') as f:
            rows = [json.loads(line) for line in f]
    except FileNotFoundError:
        print("❌ No dataset file found!")
        return
    
    print(f"📊 Total conversation turns: {len(rows)}")
    
    # Extract user and assistant messages
    user_messages = []
    assistant_messages = []
    
    for row in rows:
        messages = row['messages']
        user_msg = messages[0]['content']
        assistant_msg = messages[1]['content']
        user_messages.append(user_msg)
        assistant_messages.append(assistant_msg)
    
    # 1. Language purity check
    english_count = 0
    for row in rows:
        for msg in row['messages']:
            if re.search(r'[a-zA-Z]', msg['content']):
                english_count += 1
                break
    
    print(f"🔤 Rows with English: {english_count}/{len(rows)} ({english_count/len(rows)*100:.1f}%)")
    
    # 2. Diversity analysis
    unique_user = len(set(user_messages))
    unique_assistant = len(set(assistant_messages))
    
    print(f"🎭 User message diversity: {unique_user}/{len(rows)} ({unique_user/len(rows)*100:.1f}%)")
    print(f"🎭 Assistant response diversity: {unique_assistant}/{len(rows)} ({unique_assistant/len(rows)*100:.1f}%)")
    
    # 3. Length analysis
    user_lengths = [len(msg.split()) for msg in user_messages]
    assistant_lengths = [len(msg.split()) for msg in assistant_messages]
    
    print(f"📏 User message length - Avg: {sum(user_lengths)/len(user_lengths):.1f}, Min: {min(user_lengths)}, Max: {max(user_lengths)}")
    print(f"📏 Assistant response length - Avg: {sum(assistant_lengths)/len(assistant_lengths):.1f}, Min: {min(assistant_lengths)}, Max: {max(assistant_lengths)}")
    
    # 4. Emergency keywords analysis
    emergency_keywords = ['ایمبولینس', 'پولیس', 'فائر بریگیڈ', 'ریسکیو', 'ہسپتال', 'مدد', 'جلدی', 'حادثہ', 'آگ', 'دل کا دورہ']
    keyword_usage = {}
    
    for keyword in emergency_keywords:
        count = 0
        for row in rows:
            text = ' '.join([msg['content'] for msg in row['messages']])
            if keyword in text:
                count += 1
        keyword_usage[keyword] = count
    
    print(f"\n🚨 Emergency keyword usage:")
    for keyword, count in sorted(keyword_usage.items(), key=lambda x: x[1], reverse=True):
        print(f"  {keyword}: {count} times ({count/len(rows)*100:.1f}%)")
    
    # 5. Common response patterns
    print(f"\n🔍 Most common assistant response starts:")
    assistant_starts = [msg.split()[0] if msg.split() else '' for msg in assistant_messages]
    common_starts = Counter(assistant_starts).most_common(5)
    for start, count in common_starts:
        print(f"  '{start}': {count} times ({count/len(rows)*100:.1f}%)")
    
    # 6. Quality score calculation
    quality_score = 0
    
    # Language purity (40 points)
    purity_score = max(0, 40 - (english_count/len(rows)*40))
    quality_score += purity_score
    
    # Diversity (30 points)
    diversity_score = (unique_user/len(rows) + unique_assistant/len(rows)) * 15
    quality_score += diversity_score
    
    # Length appropriateness (20 points)
    avg_user_len = sum(user_lengths)/len(user_lengths)
    avg_assistant_len = sum(assistant_lengths)/len(assistant_lengths)
    
    if 8 <= avg_user_len <= 25 and 8 <= avg_assistant_len <= 20:
        quality_score += 20
    elif 5 <= avg_user_len <= 30 and 5 <= avg_assistant_len <= 25:
        quality_score += 15
    else:
        quality_score += 10
    
    # Emergency relevance (10 points)
    emergency_coverage = sum(1 for count in keyword_usage.values() if count > 0)
    quality_score += (emergency_coverage / len(emergency_keywords)) * 10
    
    print(f"\n⭐ Overall Quality Score: {quality_score:.1f}/100")
    
    if quality_score >= 85:
        print("✅ Excellent quality dataset! Perfect for fine-tuning.")
    elif quality_score >= 70:
        print("🟢 Good quality dataset, ready for fine-tuning.")
    elif quality_score >= 55:
        print("🟡 Decent quality, minor improvements recommended.")
    else:
        print("❌ Poor quality, significant improvements needed.")
    
    return quality_score

def show_sample_conversations():
    """Show sample conversations"""
    print("\n📝 Sample Conversations:")
    
    try:
        with open(Config.OUTPUT_FILE, 'r', encoding='utf-8') as f:
            rows = [json.loads(line) for line in f]
        
        # Show 5 random samples
        import random
        samples = random.sample(rows, min(5, len(rows)))
        
        for i, row in enumerate(samples, 1):
            messages = row['messages']
            print(f"\n--- Sample {i} ---")
            print(f"User: {messages[0]['content']}")
            print(f"Assistant: {messages[1]['content']}")
            
    except Exception as e:
        print(f"Error showing samples: {e}")

if __name__ == "__main__":
    score = analyze_conversational_quality()
    show_sample_conversations()
    
    print(f"\n🎯 Dataset Analysis Complete!")
    print(f"📁 File: {Config.OUTPUT_FILE}")
    print(f"⭐ Quality Score: {score:.1f}/100")
    
    if score >= 70:
        print("✅ This dataset is ready for Alif 8B fine-tuning!")
        print("💡 Format is perfect for conversational AI training.")
    else:
        print("⚠️  Consider regenerating with improved prompts.")