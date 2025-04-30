import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';

// Mock stamina data for visualization
const mockMatchData = {
  match_id: "day1_match3_team_a_vs_team_b",
  rounds: 10,
  characters: [
    {
      id: "char_001",
      name: "Alice",
      team: "Team A",
      stamina_log: [
        { round: 1, stamina: 100.0, event: "initial" },
        { round: 1, stamina: 95.0, event: "trait_activation:power_strike" },
        { round: 1, stamina: 91.0, event: "end_of_round_decay" },
        { round: 1, stamina: 94.0, event: "end_of_round_recovery" },
        { round: 2, stamina: 89.0, event: "capturing_piece" },
        { round: 2, stamina: 85.0, event: "end_of_round_decay" },
        { round: 2, stamina: 88.0, event: "end_of_round_recovery" },
        { round: 3, stamina: 83.0, event: "trait_activation:power_strike" },
        { round: 3, stamina: 79.0, event: "end_of_round_decay" },
        { round: 3, stamina: 82.0, event: "end_of_round_recovery" },
        { round: 4, stamina: 77.0, event: "capturing_piece" },
        { round: 4, stamina: 73.0, event: "end_of_round_decay" },
        { round: 4, stamina: 76.0, event: "end_of_round_recovery" },
        { round: 5, stamina: 71.0, event: "trait_activation:power_strike" },
        { round: 5, stamina: 66.0, event: "convergence_assist" },
        { round: 5, stamina: 62.0, event: "end_of_round_decay" },
        { round: 5, stamina: 65.0, event: "end_of_round_recovery" },
        { round: 6, stamina: 60.0, event: "capturing_piece" },
        { round: 6, stamina: 56.0, event: "end_of_round_decay" },
        { round: 6, stamina: 59.0, event: "end_of_round_recovery" },
        { round: 7, stamina: 54.0, event: "trait_activation:power_strike" },
        { round: 7, stamina: 50.0, event: "end_of_round_decay" },
        { round: 7, stamina: 53.0, event: "end_of_round_recovery" },
        { round: 8, stamina: 48.0, event: "capturing_piece" },
        { round: 8, stamina: 44.0, event: "end_of_round_decay" },
        { round: 8, stamina: 47.0, event: "end_of_round_recovery" },
        { round: 9, stamina: 42.0, event: "trait_activation:power_strike" },
        { round: 9, stamina: 38.0, event: "end_of_round_decay" },
        { round: 9, stamina: 41.0, event: "end_of_round_recovery" },
        { round: 10, stamina: 36.0, event: "capturing_piece" },
        { round: 10, stamina: 31.0, event: "convergence_assist" },
        { round: 10, stamina: 27.0, event: "end_of_round_decay" },
        { round: 10, stamina: 30.0, event: "end_of_round_recovery" }
      ],
      effects: ["stamina:minor_fatigue", "stamina:moderate_fatigue", "stamina:trait_restriction"]
    },
    {
      id: "char_002",
      name: "Bob",
      team: "Team A",
      stamina_log: [
        { round: 1, stamina: 100.0, event: "initial" },
        { round: 1, stamina: 97.0, event: "end_of_round_decay" },
        { round: 1, stamina: 100.0, event: "end_of_round_recovery" },
        { round: 2, stamina: 95.0, event: "capturing_piece" },
        { round: 2, stamina: 92.0, event: "end_of_round_decay" },
        { round: 2, stamina: 96.0, event: "end_of_round_recovery" },
        { round: 3, stamina: 91.0, event: "trait_activation:defensive_stance" },
        { round: 3, stamina: 88.0, event: "end_of_round_decay" },
        { round: 3, stamina: 92.0, event: "end_of_round_recovery" },
        { round: 4, stamina: 87.0, event: "capturing_piece" },
        { round: 4, stamina: 84.0, event: "end_of_round_decay" },
        { round: 4, stamina: 88.0, event: "end_of_round_recovery" },
        { round: 5, stamina: 83.0, event: "convergence_target" },
        { round: 5, stamina: 80.0, event: "end_of_round_decay" },
        { round: 5, stamina: 84.0, event: "end_of_round_recovery" },
        { round: 6, stamina: 79.0, event: "capturing_piece" },
        { round: 6, stamina: 76.0, event: "end_of_round_decay" },
        { round: 6, stamina: 80.0, event: "end_of_round_recovery" },
        { round: 7, stamina: 75.0, event: "trait_activation:defensive_stance" },
        { round: 7, stamina: 72.0, event: "end_of_round_decay" },
        { round: 7, stamina: 76.0, event: "end_of_round_recovery" },
        { round: 8, stamina: 71.0, event: "capturing_piece" },
        { round: 8, stamina: 68.0, event: "end_of_round_decay" },
        { round: 8, stamina: 72.0, event: "end_of_round_recovery" },
        { round: 9, stamina: 67.0, event: "trait_activation:defensive_stance" },
        { round: 9, stamina: 64.0, event: "end_of_round_decay" },
        { round: 9, stamina: 68.0, event: "end_of_round_recovery" },
        { round: 10, stamina: 63.0, event: "capturing_piece" },
        { round: 10, stamina: 60.0, event: "end_of_round_decay" },
        { round: 10, stamina: 64.0, event: "end_of_round_recovery" }
      ],
      effects: []
    },
    {
      id: "char_003",
      name: "Charlie",
      team: "Team B",
      stamina_log: [
        { round: 1, stamina: 100.0, event: "initial" },
        { round: 1, stamina: 95.0, event: "counter_attack" },
        { round: 1, stamina: 91.0, event: "end_of_round_decay" },
        { round: 1, stamina: 94.0, event: "end_of_round_recovery" },
        { round: 2, stamina: 91.0, event: "trait_activation:defensive_stance" },
        { round: 2, stamina: 87.0, event: "end_of_round_decay" },
        { round: 2, stamina: 90.0, event: "end_of_round_recovery" },
        { round: 3, stamina: 85.0, event: "counter_attack" },
        { round: 3, stamina: 81.0, event: "end_of_round_decay" },
        { round: 3, stamina: 84.0, event: "end_of_round_recovery" },
        { round: 4, stamina: 81.0, event: "trait_activation:defensive_stance" },
        { round: 4, stamina: 77.0, event: "end_of_round_decay" },
        { round: 4, stamina: 80.0, event: "end_of_round_recovery" },
        { round: 5, stamina: 75.0, event: "convergence_target" },
        { round: 5, stamina: 71.0, event: "end_of_round_decay" },
        { round: 5, stamina: 74.0, event: "end_of_round_recovery" },
        { round: 6, stamina: 69.0, event: "counter_attack" },
        { round: 6, stamina: 65.0, event: "end_of_round_decay" },
        { round: 6, stamina: 68.0, event: "end_of_round_recovery" },
        { round: 7, stamina: 63.0, event: "trait_activation:defensive_stance" },
        { round: 7, stamina: 59.0, event: "end_of_round_decay" },
        { round: 7, stamina: 62.0, event: "end_of_round_recovery" },
        { round: 8, stamina: 59.0, event: "trait_activation:defensive_stance" },
        { round: 8, stamina: 55.0, event: "end_of_round_decay" },
        { round: 8, stamina: 58.0, event: "end_of_round_recovery" },
        { round: 9, stamina: 53.0, event: "counter_attack" },
        { round: 9, stamina: 49.0, event: "end_of_round_decay" },
        { round: 9, stamina: 52.0, event: "end_of_round_recovery" },
        { round: 10, stamina: 47.0, event: "trait_activation:defensive_stance" },
        { round: 10, stamina: 43.0, event: "end_of_round_decay" },
        { round: 10, stamina: 46.0, event: "end_of_round_recovery" }
      ],
      effects: ["stamina:minor_fatigue"]
    },
    {
      id: "char_004",
      name: "Diana",
      team: "Team B",
      stamina_log: [
        { round: 1, stamina: 100.0, event: "initial" },
        { round: 1, stamina: 95.0, event: "counter_attack" },
        { round: 1, stamina: 90.0, event: "end_of_round_decay" },
        { round: 1, stamina: 93.0, event: "end_of_round_recovery" },
        { round: 2, stamina: 90.0, event: "trait_activation:power_strike" },
        { round: 2, stamina: 85.0, event: "end_of_round_decay" },
        { round: 2, stamina: 88.0, event: "end_of_round_recovery" },
        { round: 3, stamina: 83.0, event: "counter_attack" },
        { round: 3, stamina: 78.0, event: "end_of_round_decay" },
        { round: 3, stamina: 81.0, event: "end_of_round_recovery" },
        { round: 4, stamina: 76.0, event: "trait_activation:power_strike" },
        { round: 4, stamina: 71.0, event: "end_of_round_decay" },
        { round: 4, stamina: 74.0, event: "end_of_round_recovery" },
        { round: 5, stamina: 69.0, event: "counter_attack" },
        { round: 5, stamina: 64.0, event: "convergence_assist" },
        { round: 5, stamina: 59.0, event: "end_of_round_decay" },
        { round: 5, stamina: 62.0, event: "end_of_round_recovery" },
        { round: 6, stamina: 57.0, event: "counter_attack" },
        { round: 6, stamina: 52.0, event: "end_of_round_decay" },
        { round: 6, stamina: 55.0, event: "end_of_round_recovery" },
        { round: 7, stamina: 50.0, event: "trait_activation:power_strike" },
        { round: 7, stamina: 45.0, event: "end_of_round_decay" },
        { round: 7, stamina: 48.0, event: "end_of_round_recovery" },
        { round: 8, stamina: 43.0, event: "trait_activation:power_strike" },
        { round: 8, stamina: 38.0, event: "end_of_round_decay" },
        { round: 8, stamina: 41.0, event: "end_of_round_recovery" },
        { round: 9, stamina: 36.0, event: "counter_attack" },
        { round: 9, stamina: 31.0, event: "end_of_round_decay" },
        { round: 9, stamina: 34.0, event: "end_of_round_recovery" },
        { round: 10, stamina: 29.0, event: "trait_activation:power_strike" },
        { round: 10, stamina: 24.0, event: "end_of_round_decay" },
        { round: 10, stamina: 27.0, event: "end_of_round_recovery" }
      ],
      effects: ["stamina:minor_fatigue", "stamina:moderate_fatigue", "stamina:trait_restriction"]
    }
  ],
  thresholds: [
    { value: 60, label: "Minor Fatigue", effects: ["Accuracy -5%"] },
    { value: 40, label: "Moderate Fatigue", effects: ["Damage +10%", "Trait Chance -25%"] },
    { value: 20, label: "Severe Fatigue", effects: ["Damage +20%", "High-Cost Traits Locked", "5% Resignation Risk"] }
  ],
  stamina_costs: [
    { action: "standard_move", cost: 1.0 },
    { action: "trait_activation", cost: 2.0 },
    { action: "convergence_assist", cost: 3.0 },
    { action: "convergence_target", cost: 5.0 },
    { action: "counter_attack", cost: 2.5 },
    { action: "capturing_piece", cost: "Varies" }
  ]
};

// Process data for visualization
const processDataForChart = (characters) => {
  // Extract stamina values per round for each character
  const data = [];
  
  // Find max round
  const maxRound = Math.max(...characters.flatMap(char => char.stamina_log.map(log => log.round)));
  
  // For each round, get the last stamina value for each character
  for (let round = 1; round <= maxRound; round++) {
    const roundData = { round };
    
    characters.forEach(char => {
      // Get logs for this round
      const roundLogs = char.stamina_log.filter(log => log.round === round);
      
      // Get the last stamina value for this round
      if (roundLogs.length > 0) {
        const lastLog = roundLogs[roundLogs.length - 1];
        roundData[char.name] = lastLog.stamina;
      }
    });
    
    data.push(roundData);
  }
  
  return data;
};

// Process events for visualization
const processEventsForChart = (characters) => {
  // Count event types across all characters
  const eventCounts = {};
  
  characters.forEach(char => {
    char.stamina_log.forEach(log => {
      // Skip initial and round-based events
      if (log.event === "initial" || log.event.includes("end_of_round")) {
        return;
      }
      
      // Get base event type (before any colon)
      const eventType = log.event.split(':')[0];
      
      // Count events
      if (!eventCounts[eventType]) {
        eventCounts[eventType] = 0;
      }
      eventCounts[eventType]++;
    });
  });
  
  // Convert to array for chart
  return Object.entries(eventCounts).map(([name, count]) => ({
    name,
    count
  }));
};

// Calculate final stamina for color coding
const calculateFinalStamina = (characters) => {
  return characters.map(char => {
    const logs = char.stamina_log;
    const lastStamina = logs[logs.length - 1].stamina;
    
    let color = "#82ca9d"; // Default green
    
    // Color based on thresholds
    if (lastStamina <= 20) {
      color = "#ff8042"; // Orange/red
    } else if (lastStamina <= 40) {
      color = "#ffbb28"; // Yellow
    } else if (lastStamina <= 60) {
      color = "#8884d8"; // Purple
    }
    
    return {
      name: char.name,
      team: char.team,
      stamina: lastStamina,
      color: color
    };
  });
};

const StaminaVisualizer = ({ matchData = mockMatchData }) => {
  const [selectedCharacter, setSelectedCharacter] = useState("all");
  
  // Process data for charts
  const staminaData = processDataForChart(matchData.characters);
  const eventData = processEventsForChart(matchData.characters);
  const finalStaminaData = calculateFinalStamina(matchData.characters);
  
  // Generate colors for teams
  const getCharacterColor = (name) => {
    const char = matchData.characters.find(c => c.name === name);
    return char?.team === "Team A" ? "#8884d8" : "#82ca9d";
  };
  
  // Filter characters for the chart
  const filteredStaminaData = staminaData;
  
  // Handler for character selection
  const handleCharacterChange = (e) => {
    setSelectedCharacter(e.target.value);
  };
  
  // CSS colors for thresholds
  const thresholdColors = {
    60: "#8884d8",  // Purple
    40: "#ffbb28",  // Yellow
    20: "#ff8042"   // Orange
  };
  
  return (
    <div className="flex flex-col w-full p-4 bg-gray-50">
      <h1 className="text-2xl font-bold mb-4">META Fantasy League - Stamina System Visualization</h1>
      
      <div className="mb-4">
        <label className="mr-2 font-medium">Select Characters:</label>
        <select 
          value={selectedCharacter} 
          onChange={handleCharacterChange}
          className="border rounded p-1">
          <option value="all">All Characters</option>
          {matchData.characters.map(char => (
            <option key={char.id} value={char.name}>{char.name} ({char.team})</option>
          ))}
        </select>
      </div>
      
      {/* Stamina Chart */}
      <div className="bg-white p-4 rounded shadow mb-6">
        <h2 className="text-xl font-semibold mb-2">Stamina Levels by Round</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={filteredStaminaData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="round" label={{ value: 'Round', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'Stamina', angle: -90, position: 'insideLeft' }} domain={[0, 100]} />
            <Tooltip />
            <Legend />
            
            {/* Add threshold reference lines */}
            {matchData.thresholds.map(threshold => (
              <CartesianGrid 
                key={threshold.value} 
                y={threshold.value} 
                stroke={thresholdColors[threshold.value]} 
                strokeDasharray="3 3" />
            ))}
            
            {/* Display lines for selected characters */}
            {matchData.characters
              .filter(char => selectedCharacter === "all" || char.name === selectedCharacter)
              .map(char => (
                <Line 
                  key={char.id}
                  type="monotone" 
                  dataKey={char.name} 
                  stroke={getCharacterColor(char.name)}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              ))}
          </LineChart>
        </ResponsiveContainer>
        
        {/* Threshold legend */}
        <div className="mt-2 flex flex-wrap gap-4">
          {matchData.thresholds.map(threshold => (
            <div key={threshold.value} className="flex items-center">
              <div
                className="w-4 h-4 mr-2"
                style={{ backgroundColor: thresholdColors[threshold.value] }}
              ></div>
              <span className="text-sm">
                {threshold.label} ({threshold.value}): {threshold.effects.join(", ")}
              </span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Event Chart and Final Stamina */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-semibold mb-2">Stamina Costs by Action Type</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={eventData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#8884d8">
                {eventData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={`#${(index * 4 + 2) * 111}`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          
          {/* Action cost table */}
          <div className="mt-4">
            <h3 className="font-medium mb-1">Standard Stamina Costs:</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-1">Action</th>
                  <th className="text-right py-1">Cost</th>
                </tr>
              </thead>
              <tbody>
                {matchData.stamina_costs.map((cost, i) => (
                  <tr key={i} className="border-b">
                    <td className="py-1">{cost.action}</td>
                    <td className="text-right py-1">{cost.cost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Final Stamina State */}
        <div className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-semibold mb-2">Final Stamina State</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={finalStaminaData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 100]} />
              <YAxis dataKey="name" type="category" width={80} />
              <Tooltip />
              <Legend />
              <Bar dataKey="stamina" name="Final Stamina">
                {finalStaminaData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          
          {/* Character effects table */}
          <div className="mt-4">
            <h3 className="font-medium mb-1">Active Effects:</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-1">Character</th>
                  <th className="text-left py-1">Team</th>
                  <th className="text-left py-1">Effects</th>
                </tr>
              </thead>
              <tbody>
                {matchData.characters.map(char => (
                  <tr key={char.id} className="border-b">
                    <td className="py-1">{char.name}</td>
                    <td className="py-1">{char.team}</td>
                    <td className="py-1">
                      {char.effects.length > 0 
                        ? char.effects.map(e => e.split(':')[1]).join(", ")
                        : "None"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      
      <div className="mt-6 text-sm text-gray-600">
        <p>
          This visualization demonstrates the META Fantasy League Stamina System in action.
          Characters lose stamina through various actions and recover a portion each round.
          As stamina decreases below thresholds, characters experience different levels of fatigue effects.
        </p>
      </div>
    </div>
  );
};

export default StaminaVisualizer;
