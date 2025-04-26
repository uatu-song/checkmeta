#!/usr/bin/env python3
"""
Sally Floyd Narrative Generator
A post-processing tool to analyze META Fantasy League match results
and generate narrative reports based on rStats and other match data.
"""

import os
import json
import datetime
import random
import pandas as pd
import argparse

# Team name mapping for more readable reports - using the ACTUAL team names
friendly_name_map = {
    'tT001': "Gambit Is A Pretty Pretty Princess", 
    'tT002': "Costco Wholesale",
    'tT003': "Sterling's Silly Soldiers",
    'tT004': "Dumb and Dumber Returns",
    'tT005': "Ligmasigma II",
    'tT006': "Pigeon Desk",
    'tT007': "Agents of Vishanti",
    'tT008': "Slow And Threatening",
    'tT009': "Amber",
    'tT010': "Your honor, we were just being silly"
}

def extract_stats_from_results(results_file):
    """
    Extract statistics from match results JSON file
    """
    with open(results_file, 'r') as f:
        match_results = json.load(f)
    
    # Extract character stats from all matches
    all_char_stats = []
    match_summaries = []
    
    for match_idx, match in enumerate(match_results):
        # Map team names to their friendly names
        team_a_id = match["team_a_name"].replace("Team ", "t")
        team_b_id = match["team_b_name"].replace("Team ", "t")
        team_a_friendly = friendly_name_map.get(team_a_id, match["team_a_name"])
        team_b_friendly = friendly_name_map.get(team_b_id, match["team_b_name"])
        
        # Get winning team name
        winning_team_name = "None"
        if match["winning_team"] != "None":
            winning_team_id = match["winning_team"].replace("Team ", "t")
            winning_team_name = friendly_name_map.get(winning_team_id, match["winning_team"])
        
        # Track match-level stats
        match_summaries.append({
            "team_a_name": team_a_friendly,
            "team_b_name": team_b_friendly,
            "team_a_wins": match["team_a_wins"],
            "team_b_wins": match["team_b_wins"],
            "winner": match["winner"],
            "winning_team": winning_team_name,
            "convergence_count": match.get("convergence_count", 0),
            "trait_activations": match.get("trait_activations", 0),
            "substitutions": match.get("substitutions", [])
        })
        
        for char_result in match["character_results"]:
            # Skip bench players for most analyses
            if char_result["result"] == "bench":
                continue
                
            # Extract team ID from character ID
            team_id = char_result["character_id"].split("_")[0]
            
            # Calculate damage sustained from HP differences
            damage_sustained = 100 - char_result["final_hp"]
            
            # Get rStats if available, otherwise use empty dict
            rstats = char_result.get("rStats", {})
            
            # Extract key rStats or set defaults
            dd = rstats.get("rDD", 0)  # Damage Dealt
            ds = rstats.get("rDS", damage_sustained)  # Damage Sustained
            ult = rstats.get("rULT", 0)  # Ultimate Moves
            mbi = rstats.get("rMBi", 0)  # Mind Break (intelligence)
            lvs = rstats.get("rLVS", 0)  # Lives Saved
            hlg = rstats.get("rHLG", 0)  # Healing
            knb = rstats.get("rKNB", 0)  # Knockout Blow

            # If rStats are not available, infer some from the data
            if not rstats:
                # Infer damage dealt based on result and HP
                dd = damage_sustained * 2 if char_result["result"] == "win" else damage_sustained / 2
                
            # Create stat record
            char_stats = {
                "name": char_result["character_name"],
                "team": team_id,
                "team_name": friendly_name_map.get(team_id, team_id),
                "role": char_result["role"],
                "HP": char_result["final_hp"],
                "stamina": char_result["final_stamina"],
                "life": char_result["final_life"],
                "is_ko": char_result["is_ko"],
                "result": char_result["result"],
                "was_substituted": char_result.get("substituted", False),
                "match_idx": match_idx,
                # Use rStats or inferred stats
                "DD": dd,
                "DS": ds,
                "ULT": ult,
                "MBi": mbi,
                "LVS": lvs,
                "HLG": hlg,
                "KNB": knb,
                # Default XP based on result
                "XP": 25 if char_result["result"] == "win" else 10 if char_result["result"] == "draw" else 5,
                "KO": 1 if char_result["is_ko"] else 0
            }
            all_char_stats.append(char_stats)
    
    return pd.DataFrame(all_char_stats), match_summaries

def generate_sally_report(match_logs, match_summaries, match_date=None):
    """
    Generate a Sally Floyd narrative report from match statistics
    
    Args:
        match_logs (DataFrame): Character statistics 
        match_summaries (list): Match-level summary data
        match_date (datetime): Date of the match
        
    Returns:
        dict: Narrative report sections
    """
    if match_date is None:
        match_date = datetime.datetime.now()
    
    # Find interesting characters and events for storytelling
    
    # Top damage dealer
    try:
        top_dd = match_logs.sort_values(by="DD", ascending=False).iloc[0]
    except:
        top_dd = {"name": "Unknown", "team_name": "Unknown Team", "DD": 0}
    
    # Most damaged character that survived
    try:
        survivors = match_logs[match_logs["is_ko"] == False]
        top_damaged = survivors.sort_values(by="DS", ascending=False).iloc[0]
    except:
        top_damaged = {"name": "Unknown", "team_name": "Unknown Team", "DS": 0}
    
    # Character with most Ultimate moves
    try:
        top_ult = match_logs.sort_values(by="ULT", ascending=False)
        if len(top_ult) > 0 and top_ult.iloc[0]["ULT"] > 0:
            top_ult = top_ult.iloc[0]
        else:
            top_ult = None
    except:
        top_ult = None
    
    # Intelligence division character with Mind Breaks
    try:
        mind_breakers = match_logs[match_logs["MBi"] > 0].sort_values(by="MBi", ascending=False)
        if len(mind_breakers) > 0:
            top_mbi = mind_breakers.iloc[0]
        else:
            top_mbi = None
    except:
        top_mbi = None
    
    # Character who saved lives
    try:
        lifesavers = match_logs[match_logs["LVS"] > 0].sort_values(by="LVS", ascending=False)
        if len(lifesavers) > 0:
            top_lvs = lifesavers.iloc[0]
        else:
            top_lvs = None
    except:
        top_lvs = None
    
    # Character who healed the most
    try:
        healers = match_logs[match_logs["HLG"] > 0].sort_values(by="HLG", ascending=False)
        if len(healers) > 0:
            top_hlg = healers.iloc[0]
        else:
            top_hlg = None
    except:
        top_hlg = None
    
    # Find the match with the most trait activations
    max_traits_match = max(match_summaries, key=lambda x: x.get("trait_activations", 0))
    
    # Find the match with the most substitutions
    max_subs_match = max(match_summaries, key=lambda x: len(x.get("substitutions", [])))
    
    # Check if there were any double substitutions (one team had to sub twice)
    double_subs = None
    for match in match_summaries:
        subs = match.get("substitutions", [])
        if len(subs) >= 2:
            # Check if same team subbed twice
            team_a_subs = sum(1 for sub in subs if sub["ko_character"] in [char["name"] for char in match_logs[match_logs["team"] == match["team_a_name"]].to_dict('records')])
            team_b_subs = sum(1 for sub in subs if sub["ko_character"] in [char["name"] for char in match_logs[match_logs["team"] == match["team_b_name"]].to_dict('records')])
            
            if team_a_subs >= 2:
                double_subs = match["team_a_name"]
                break
            elif team_b_subs >= 2:
                double_subs = match["team_b_name"]
                break
    
    # Generate narrative sections based on the data we found
    
    # CINEMATIC: Describes a high damage moment
    cinematic_options = [
        f"{top_dd['name']} of {top_dd['team_name']} unleashed {int(top_dd['DD'])} damage — most of the league froze just watching.",
        f"When {top_dd['name']} launched their attack, the damage indicators spiked to {int(top_dd['DD'])}. The crowd went silent.",
        f"The arena screens flashed red when {top_dd['name']} hit for {int(top_dd['DD'])} — I've never seen the meters go that high.",
        f"{top_dd['name']} dealt {int(top_dd['DD'])} in a single convergence. Half the observers thought the sim was glitching."
    ]
    cinematic = random.choice(cinematic_options)
    
    # TRAGEDY: Focus on knockouts, substitutions, or near-deaths
    if double_subs:
        tragedy = f"{double_subs} lost two Field Leaders in a single match. The medical team was overwhelmed with the carnage."
    elif len(max_subs_match.get("substitutions", [])) > 0:
        sub = max_subs_match["substitutions"][0]
        tragedy = f"{sub['ko_character']} collapsed on round {sub['round']}. {sub['replacement']} stepped in, but the momentum was already broken."
    else:
        tragedy = f"{top_damaged['name']} absorbed {int(top_damaged['DS'])} damage but refused to fall. The med team was shocked they were still standing."
    
    # BROKEN TIMELINE: Focus on anomalies, Mind Breaks, or strange patterns
    if mind_breakers is not None and len(mind_breakers) >= 2:
        mbi1 = mind_breakers.iloc[0]
        mbi2 = mind_breakers.iloc[1]
        broken = f"{mbi1['name']} and {mbi2['name']} triggered simultaneous MBi flashes — no one's sure what the Overlay saw, but the Undercurrent twitched."
    elif top_mbi is not None:
        broken = f"When {top_mbi['name']} triggered a Mind Break, the baseline reality stuttered. The refs spent three minutes debating if the match should continue."
    elif top_ult is not None:
        broken = f"{top_ult['name']}'s Ultimate triggered {top_ult['ULT']} times in a single match. The probability engines are still trying to make sense of it."
    else:
        broken = f"The convergence patterns today showed abnormal clustering. It's almost like the system was trying to maximize damage in certain zones."
    
    # TRAIT GLITCHES: Reference to trait activations, healing, or other special abilities
    if top_hlg is not None:
        traits = f"{top_hlg['name']} channeled {int(top_hlg['HLG'])} in healing energy. The grid lit up like New Year's Eve as the traits cascaded."
    elif top_lvs is not None:
        traits = f"{top_lvs['name']} saved {int(top_lvs['LVS'])} teammates from critical status. Their traits kept flaring in unusual sequences."
    else:
        traits = f"Match {max_traits_match['team_a_name']} vs {max_traits_match['team_b_name']} triggered {max_traits_match['trait_activations']} traits. The grid burned like it was finals week."
    
    # OVERLAY VS UNDERCURRENT: Focus on substitutions or other anomalies
    overlays_options = [
        "One sim log shows Nova KO'd. Another shows him KO'ing. Sally can't verify either.",
        f"The {match_summaries[0]['winning_team']} win doesn't match my baseline predictions. Either the sim is evolving or someone's adjusting parameters.",
        f"Convergence patterns don't match last week's baseline. Something's shifted in how the grid processes character interactions.",
        f"Trait activations up {max(0, max_traits_match['trait_activations'] - 3000)}% from normal. Either someone's gaming the system or the characters are adapting."
    ]
    overlays = random.choice(overlays_options)
    
    # Famous quotes
    quotes = [
        "I saw what I saw. Doesn't mean I understood it.",
        "We logged it. The sim denied it. Typical Tuesday.",
        "If reality's fraying, I hope I'm at least writing in the margins.",
        "Some days the digital and the real blur too much for comfort.",
        "The baseline slipped again. No one noticed except me.",
        "Field Leaders falling, Sovereigns rising. The patterns don't match anymore.",
        "Who watches the watchers? Me. I watch them. Someone has to.",
        "These aren't 'bugs in the system'. They're features of a deeper reality.",
        "When the convergence hits triple digits, the probability fields start to fold in on themselves.",
        "Four thousand trait activations in one match? That's not a coincidence. That's a message."
    ]

    # Random opening paragraphs
    openings = [
        "Today, the Nexus battlefield felt cracked — not broken, not bent, just... trembling. Fighters blinked through timelines, and half the crowd was watching something that wasn't happening yet.",
        "The sim operators kept resetting their equipment today. According to their instruments, several fighters were in two places at once.",
        "Quantum variance off the charts this morning. We're seeing timeline instability in ways the oversight committee won't acknowledge.",
        "They keep telling me the system is stable. I keep telling them what I see. Someone's lying, and I don't think it's me.",
        "Field analysis showed temporal fragmentation during three matches today. I flagged it. They ignored it. Standard protocol.",
        "The nexus grid is showing unusual patterns. Nexus Beings who shouldn't be able to converge did so 23% more often than baseline.",
        "Four matches, over four thousand trait activations, and nobody thinks that's strange? I'm the only one keeping count.",
        "Something's wrong with the probability fields. Outcomes that should be impossible are happening regularly now."
    ]

    return {
        "match_date": match_date.strftime("%B %d, %Y"),
        "overlay_date": match_date.strftime("Week %W"),
        "undercurrent_code": f"UC-{match_date.strftime('%Y%m%d')}-FLOYD",
        "opening_paragraph": random.choice(openings),
        "cinematic_moment": cinematic,
        "broken_moment": broken,
        "tragedy_moment": tragedy,
        "trait_glitches": traits,
        "overlay_vs_undercurrent": overlays,
        "closing_quote": random.choice(quotes)
    }

def save_report(report, output_file):
    """
    Save the narrative report to a text file
    """
    with open(output_file, "w") as f:
        f.write(f"Narrative Match Report - {report['match_date']} ({report['overlay_date']})\n")
        f.write(f"Undercurrent Code: {report['undercurrent_code']}\n\n")
        f.write(f"{report['opening_paragraph']}\n\n")
        f.write(f"CINEMATIC: {report['cinematic_moment']}\n")
        f.write(f"TRAGEDY: {report['tragedy_moment']}\n")
        f.write(f"BROKEN TIMELINE: {report['broken_moment']}\n")
        f.write(f"TRAIT GLITCHES: {report['trait_glitches']}\n")
        f.write(f"OVERLAY v UNDERCURRENT: {report['overlay_vs_undercurrent']}\n\n")
        f.write(f"QUOTE: {report['closing_quote']}\n")
    
    return output_file

def main():
    """
    Main function to process command line arguments and generate reports
    """
    parser = argparse.ArgumentParser(description='Generate Sally Floyd narrative reports from match results')
    parser.add_argument('results_file', help='Path to the match results JSON file')
    parser.add_argument('--output', '-o', help='Output file for the narrative report')
    parser.add_argument('--date', '-d', help='Match date (default: today)', default=None)
    
    args = parser.parse_args()
    
    # Ensure results file exists
    if not os.path.exists(args.results_file):
        print(f"Error: Results file not found: {args.results_file}")
        return 1
    
    # Extract stats from results
    try:
        match_logs, match_summaries = extract_stats_from_results(args.results_file)
        print(f"Processed {len(match_summaries)} matches with {len(match_logs)} active characters")
    except Exception as e:
        print(f"Error processing results file: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Set match date
    if args.date:
        try:
            match_date = datetime.datetime.strptime(args.date, "%Y-%m-%d")
        except:
            print(f"Error: Invalid date format. Use YYYY-MM-DD")
            match_date = datetime.datetime.now()
    else:
        match_date = datetime.datetime.now()
    
    # Generate report
    report = generate_sally_report(match_logs, match_summaries, match_date)
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        # Create results/narrative directory if it doesn't exist
        os.makedirs("results/narrative", exist_ok=True)
        
        # Default filename based on date
        timestamp = match_date.strftime("%Y%m%d")
        output_file = f"results/narrative/sally_report_{timestamp}.txt"
    
    # Save report
    saved_file = save_report(report, output_file)
    print(f"Narrative report saved to: {saved_file}")
    
    return 0

if __name__ == "__main__":
    exit(main())