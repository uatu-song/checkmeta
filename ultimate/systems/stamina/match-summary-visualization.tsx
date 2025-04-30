import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';

// Sample match summary data with stamina information
const sampleMatchData = {
  match_id: "day1_match1_team_a_vs_team_b",
  day: 1,
  match_number: 1,
  team_a_name: "Team Alpha",
  team_b_name: "Team Beta",
  team_a_id: "team_a",
  team_b_id: "team_b",
  result: "win",
  winning_team: "Team Alpha",
  stamina_summary: {
    team_a_avg_stamina: 55.0,
    team_b_avg_stamina: 25.0,
    team_a_effects: {
      minor_fatigue: 1,
      moderate_fatigue: 1,
      severe_fatigue: 0
    },
    team_b_effects: {
      minor_fatigue: 2,
      moderate_fatigue: 2, 
      severe_fatigue: 1
    },
    highest_stamina_a: {
      character_name: "Alice",
      stamina: 65.0
    },
    lowest_stamina_a: {
      character_name: "Bob",
      stamina: 45.0
    },
    highest_stamina_b: {
      character_name: "Charlie",
      stamina: 35.0
    },
    lowest_stamina_b: {
      character_name: "Diana",
      stamina: 15.0
    },
    event_counts: {
      "trait_activation": 6,
      "convergence_assist": 2,
      "convergence_target": 2,
      "standard_move": 24,
      "end_of_round_decay": 40,
      "end_of_round_recovery": 40
    },
    stamina_advantage: "A"
  },
  character_results: [
    {
      character_id: "char_a1",
      character_name: "Alice",
      team: "A",
      team_id: "team_a",
      was_active: true,
      is_ko: false,
      HP: 80,
      stamina: 65,
      result: "win",
      effects: [],
      stamina_details: {
        status: "Minor Fatigue",
        initial: 100.0,
        final: 65.0,
        drained: 35.0,
        drained_percent: 35.0,
        highest_cost: 5.0,
        highest_cost_event: "trait_activation:power_strike",
        recovery_gained: 25.0,
        trait_constraint: "None"
      }
    },
    {
      character_id: "char_a2",
      character_name: "Bob",
      team: "A",
      team_id: "team_a",
      was_active: true,
      is_ko: false,
      HP: 70,
      stamina: 45,
      result: "win",
      effects: ["stamina:minor_fatigue", "stamina:trait_restriction"],
      stamina_details: {
        status: "Moderate Fatigue",
        initial: 100.0,
        final: 45.0,
        drained: 55.0,
        drained_percent: 55.0,
        highest_cost: 4.0,
        highest_cost_event: "trait_activation:defensive_stance",
        recovery_gained: 20.0,
        trait_constraint: "Reduced Chance"
      }
    },
    {
      character_id: "char_b1",
      character_name: "Charlie",
      team: "B",
      team_id: "team_b",
      was_active: true,
      is_ko: false,
      HP: 60,
      stamina: 35,
      result: "loss",
      effects: ["stamina:minor_fatigue", "stamina:moderate_fatigue"],
      stamina_details: {
        status: "Moderate Fatigue",
        initial: 100.0,
        final: 35.0,
        drained: 65.0,
        drained_percent: 65.0,
        highest_cost: 4.5,
        highest_cost_event: "counter_attack",
        recovery_gained: 18.0,
        trait_constraint: "Reduced Chance"
      }
    },
    {
      character_id: "char_b2",
      character_name: "Diana",
      team: "B",
      team_id: "team_b",
      was_active: true,
      is_ko: true,
      HP: 0,
      stamina: 15,
      result: "loss",
      effects: ["stamina:minor_fatigue", "stamina:moderate_fatigue", "stamina:severe_fatigue"],
      stamina_details: {
        status: "Severe Fatigue",
        initial: 100.0,
        final: 15.0,
        drained: 85.0,
        drained_percent: 85.0,
        highest_cost: 8.0,
        highest_cost_event: "convergence_target",
        recovery_gained: 15.0,
        trait_constraint: "High-Cost Locked"
      }
    }
  ],
  key_events: [
    {
      type: "stamina",
      character_id: "char_a1",
      character_name: "Alice",
      team_id: "team_a",
      turn: 3,
      description: "Alice expended 5.0 stamina for trait_activation:power_strike"
    },
    {
      type: "stamina",
      character_id: "char_b2",
      character_name: "Diana",
      team_id: "team_b",
      turn: 5,
      description: "Diana expended 8.0 stamina for convergence_target"
    },
    {
      type: "stamina",
      character_id: "char_b2",
      character_name: "Diana",
      team_id: "team_b",
      turn: 7,
      description: "Diana entered moderate fatigue state with 38 stamina remaining"
    },
    {
      type: "stamina",
      character_id: "char_b2",
      character_name: "Diana",
      team_id: "team_b",
      turn: 9,
      description: "Diana entered severe fatigue state with 19 stamina remaining"
    }
  ]
};

// Create data for round-by-round stamina visualization
const createRoundByRoundData = () => {
  // In a real implementation, this would read from stamina_logs
  // For the sample, we'll create synthetic data
  const rounds = 10;
  const data = [];
  
  const characters = sampleMatchData.character_results;
  
  for (let round = 0; round <= rounds; round++) {
    const roundData = { round };
    
    characters.forEach(char => {
      // Linear interpolation between initial and final stamina
      if (round === 0) {
        roundData[char.character_name] = char.stamina_details.initial;
      } else if (round === rounds) {
        roundData[char.character_name] = char.stamina_details.final;
      } else {
        // Add some randomness to make it look more realistic
        const decline = char.stamina_details.drained / rounds;
        const remainingStamina = char.stamina_details.initial - (decline * round);
        // Add some noise to make it look more natural
        const noise = Math.sin(round * 0.7) * 3; 
        roundData[char.character_name] = Math.max(0, Math.min(100, remainingStamina + noise));
      }
    });
    
    data.push(roundData);
  }
  
  return data;
};

// Extract event type counts for visualization
const createActionCostChart = () => {
  const eventData = [];
  const eventCounts = sampleMatchData.stamina_summary.event_counts;
  
  // Filter out end-of-round events as they're standard
  for (const [event, count] of Object.entries(eventCounts)) {
    if (!event.includes("end_of_round")) {
      eventData.push({
        name: event,
        count
      });
    }
  }
  
  return eventData.sort((a, b) => b.count - a.count);
};

// Extract fatigue effects by team
const createFatigueEffectsChart = () => {
  const teamA = {
    name: sampleMatchData.team_a_name,
    minor: sampleMatchData.stamina_summary.team_a_effects.minor_fatigue,
    moderate: sampleMatchData.stamina_summary.team_a_effects.moderate_fatigue,
    severe: sampleMatchData.stamina_summary.team_a_effects.severe_fatigue
  };
  
  const teamB = {
    name: sampleMatchData.team_b_name,
    minor: sampleMatchData.stamina_summary.team_b_effects.minor_fatigue,
    moderate: sampleMatchData.stamina_summary.team_b_effects.moderate_fatigue,
    severe: sampleMatchData.stamina_summary.team_b_effects.severe_fatigue
  };
  
  return [teamA, teamB];
};

// Create character final stamina comparison chart
const createCharacterFinalStaminaChart = () => {
  return sampleMatchData.character_results.map(char => {
    // Determine color based on fatigue state
    let color = '#4CAF50'; // Green for normal
    if (char.stamina_details.status === "Severe Fatigue") {
      color = '#F44336'; // Red
    } else if (char.stamina_details.status === "Moderate Fatigue") {
      color = '#FF9800'; // Orange
    } else if (char.stamina_details.status === "Minor Fatigue") {
      color = '#2196F3'; // Blue
    }
    
    return {
      name: char.character_name,
      team: char.team === "A" ? sampleMatchData.team_a_name : sampleMatchData.team_b_name,
      stamina: char.stamina,
      color
    };
  }).sort((a, b) => b.stamina - a.stamina);
};

const MatchSummaryStaminaViz = () => {
  const [activeTab, setActiveTab] = useState('overview');
  
  // Generate data for charts
  const roundByRoundData = createRoundByRoundData();
  const actionCostData = createActionCostChart();
  const fatigueEffectsData = createFatigueEffectsChart();
  const characterStaminaData = createCharacterFinalStaminaChart();
  
  // Colors for teams
  const teamColors = {
    [sampleMatchData.team_a_name]: '#8884d8', // Purple
    [sampleMatchData.team_b_name]: '#82ca9d'  // Green
  };
  
  // CSS colors for thresholds
  const thresholdColors = {
    severe: '#F44336',   // Red
    moderate: '#FF9800', // Orange
    minor: '#2196F3'     // Blue
  };
  
  return (
    <div className="flex flex-col w-full p-4 bg-gray-50">
      <h1 className="text-2xl font-bold mb-2">Match Stamina Analysis</h1>
      <h2 className="text-xl mb-4">{sampleMatchData.team_a_name} vs. {sampleMatchData.team_b_name}</h2>
      
      {/* Navigation Tabs */}
      <div className="flex space-x-2 mb-4">
        <button 
          className={`px-4 py-2 rounded ${activeTab === 'overview' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('overview')}>
          Overview
        </button>
        <button 
          className={`px-4 py-2 rounded ${activeTab === 'round-by-round' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('round-by-round')}>
          Round by Round
        </button>
        <button 
          className={`px-4 py-2 rounded ${activeTab === 'characters' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('characters')}>
          Characters
        </button>
        <button 
          className={`px-4 py-2 rounded ${activeTab === 'events' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          onClick={() => setActiveTab('events')}>
          Key Events
        </button>
      </div>
      
      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Team Comparison Card */}
          <div className="bg-white p-4 rounded shadow-md">
            <h3 className="text-lg font-semibold mb-2">Team Stamina Comparison</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="border p-3 rounded">
                <h4 className="font-medium">{sampleMatchData.team_a_name}</h4>
                <p className="text-2xl font-bold">{sampleMatchData.stamina_summary.team_a_avg_stamina}%</p>
                <p className="text-sm text-gray-600">Average Stamina</p>
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-blue-600 h-2.5 rounded-full" 
                      style={{ width: `${sampleMatchData.stamina_summary.team_a_avg_stamina}%` }}>
                    </div>
                  </div>
                </div>
              </div>
              <div className="border p-3 rounded">
                <h4 className="font-medium">{sampleMatchData.team_b_name}</h4>
                <p className="text-2xl font-bold">{sampleMatchData.stamina_summary.team_b_avg_stamina}%</p>
                <p className="text-sm text-gray-600">Average Stamina</p>
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-green-600 h-2.5 rounded-full" 
                      style={{ width: `${sampleMatchData.stamina_summary.team_b_avg_stamina}%` }}>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-4">
              <p className="font-medium">
                Stamina Advantage: {sampleMatchData.stamina_summary.stamina_advantage === "A" ? 
                  sampleMatchData.team_a_name : sampleMatchData.team_b_name}
              </p>
            </div>
          </div>
          
          {/* Fatigue Effects Chart */}
          <div className="bg-white p-4 rounded shadow-md">
            <h3 className="text-lg font-semibold mb-2">Fatigue Effects</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart 
                data={fatigueEffectsData}
                layout="vertical"
                margin={{top: 5, right: 30, left: 40, bottom: 5}}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number"/>
                <YAxis dataKey="name" type="category" width={80} />
                <Tooltip />
                <Legend />
                <Bar dataKey="minor" name="Minor Fatigue" fill={thresholdColors.minor} />
                <Bar dataKey="moderate" name="Moderate Fatigue" fill={thresholdColors.moderate} />
                <Bar dataKey="severe" name="Severe Fatigue" fill={thresholdColors.severe} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          
          {/* Character Final Stamina */}
          <div className="bg-white p-4 rounded shadow-md">
            <h3 className="text-lg font-semibold mb-2">Character Final Stamina</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart 
                data={characterStaminaData}
                layout="vertical"
                margin={{top: 5, right: 30, left: 20, bottom: 5}}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]}/>
                <YAxis dataKey="name" type="category" width={80} />
                <Tooltip />
                <Legend />
                <Bar dataKey="stamina" name="Final Stamina">
                  {characterStaminaData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-2">
              <div className="flex space-x-4">
                <div className="flex items-center">
                  <div className="w-4 h-4 mr-1" style={{ backgroundColor: '#4CAF50' }}></div>
                  <span className="text-xs">Normal</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-4 mr-1" style={{ backgroundColor: '#2196F3' }}></div>
                  <span className="text-xs">Minor Fatigue</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-4 mr-1" style={{ backgroundColor: '#FF9800' }}></div>
                  <span className="text-xs">Moderate Fatigue</span>
                </div>
                <div className="flex items-center">
                  <div className="w-4 h-4 mr-1" style={{ backgroundColor: '#F44336' }}></div>
                  <span className="text-xs">Severe Fatigue</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Round-by-Round Tab */}
      {activeTab === 'round-by-round' && (
        <div className="bg-white p-4 rounded shadow-md">
          <h3 className="text-lg font-semibold mb-2">Stamina Levels by Round</h3>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={roundByRoundData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="round" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value) => value.toFixed(1) + '%'} />
              <Legend />
              
              {/* Add threshold lines */}
              <CartesianGrid y={60} stroke="#2196F3" strokeDasharray="3 3" />
              <CartesianGrid y={40} stroke="#FF9800" strokeDasharray="3 3" />
              <CartesianGrid y={20} stroke="#F44336" strokeDasharray="3 3" />
              
              {sampleMatchData.character_results.map(char => (
                <Line
                  key={char.character_id}
                  type="monotone"
                  dataKey={char.character_name}
                  stroke={teamColors[char.team === "A" ? sampleMatchData.team_a_name : sampleMatchData.team_b_name]}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-2">
            <div className="flex space-x-4">
              <div className="flex items-center">
                <div className="w-4 h-4 mr-1" style={{ backgroundColor: '#2196F3' }}></div>
                <span className="text-xs">Minor Fatigue Threshold (60%)</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 mr-1" style={{ backgroundColor: '#FF9800' }}></div>
                <span className="text-xs">Moderate Fatigue Threshold (40%)</span>
              </div>
              <div className="flex items-center">
                <div className="w-4 h-4 mr-1" style={{ backgroundColor: '#F44336' }}></div>
                <span className="text-xs">Severe Fatigue Threshold (20%)</span>
              </div>
            </div>
          </div>
          
          {/* Action costs chart */}
          <div className="mt-6">
            <h3 className="text-lg font-semibold mb-2">Action Costs</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart 
                data={actionCostData}
                margin={{top: 5, right: 30, left: 20, bottom: 5}}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#8884d8" name="Occurrences">
                  {actionCostData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={`#${(index * 4 + 2) * 111}`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      
      {/* Characters Tab */}
      {activeTab === 'characters' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sampleMatchData.character_results.map(char => (
            <div key={char.character_id} className="bg-white p-4 rounded shadow-md">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold">
                    {char.character_name}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {char.team === "A" ? sampleMatchData.team_a_name : sampleMatchData.team_b_name}
                  </p>
                </div>
                <div className={`px-2 py-1 rounded text-white text-sm ${
                  char.stamina_details.status === "Severe Fatigue" ? "bg-red-500" :
                  char.stamina_details.status === "Moderate Fatigue" ? "bg-orange-500" :
                  char.stamina_details.status === "Minor Fatigue" ? "bg-blue-500" :
                  "bg-green-500"
                }`}>
                  {char.stamina_details.status}
                </div>
              </div>
              
              {/* Stamina gauge */}
              <div className="mt-3">
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Stamina</span>
                  <span className="text-sm font-medium">{char.stamina}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    className={`h-2.5 rounded-full ${
                      char.stamina_details.status === "Severe Fatigue" ? "bg-red-500" :
                      char.stamina_details.status === "Moderate Fatigue" ? "bg-orange-500" :
                      char.stamina_details.status === "Minor Fatigue" ? "bg-blue-500" :
                      "bg-green-500"
                    }`}
                    style={{ width: `${char.stamina}%` }}>
                  </div>
                </div>
              </div>
              
              {/* Stamina stats */}
              <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
                <div>
                  <p className="text-gray-600">Initial</p>
                  <p className="font-medium">{char.stamina_details.initial}%</p>
                </div>
                <div>
                  <p className="text-gray-600">Drained</p>
                  <p className="font-medium">{char.stamina_details.drained_percent}%</p>
                </div>
                <div>
                  <p className="text-gray-600">Recovery</p>
                  <p className="font-medium">{char.stamina_details.recovery_gained}%</p>
                </div>
              </div>
              
              {/* Effects and constraints */}
              <div className="mt-4">
                <p className="text-gray-600 text-sm">Active Effects</p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {char.effects.length > 0 ? char.effects.map((effect, index) => (
                    <span 
                      key={index} 
                      className="px-2 py-1 bg-gray-100 rounded text-xs">
                      {effect.split(':')[1]}
                    </span>
                  )) : (
                    <span className="text-sm text-gray-500">None</span>
                  )}
                </div>
              </div>
              
              {/* Highest cost action */}
              <div className="mt-4">
                <p className="text-gray-600 text-sm">Highest Cost Action</p>
                <p className="font-medium">
                  {char.stamina_details.highest_cost_event} ({char.stamina_details.highest_cost}%)
                </p>
              </div>
              
              {/* Trait constraints */}
              <div className="mt-4">
                <p className="text-gray-600 text-sm">Trait Constraint</p>
                <p className={`font-medium ${
                  char.stamina_details.trait_constraint === "None" ? "text-green-600" :
                  char.stamina_details.trait_constraint === "Reduced Chance" ? "text-orange-600" :
                  "text-red-600"
                }`}>
                  {char.stamina_details.trait_constraint}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Key Events Tab */}
      {activeTab === 'events' && (
        <div className="bg-white p-4 rounded shadow-md">
          <h3 className="text-lg font-semibold mb-4">Key Stamina Events</h3>
          
          <div className="flex flex-col space-y-4">
            {sampleMatchData.key_events
              .filter(event => event.type === "stamina")
              .sort((a, b) => a.turn - b.turn)
              .map((event, index) => (
                <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                  <div className="flex justify-between">
                    <span className="font-medium">Round {event.turn}</span>
                    <span className="text-sm text-gray-600">
                      {event.character_name} ({event.team_id === "team_a" ? sampleMatchData.team_a_name : sampleMatchData.team_b_name})
                    </span>
                  </div>
                  <p className="mt-1">{event.description}</p>
                </div>
              ))}
          </div>
          
          {sampleMatchData.key_events.filter(event => event.type === "stamina").length === 0 && (
            <p className="text-center text-gray-500 py-4">No key stamina events recorded.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default MatchSummaryStaminaViz;