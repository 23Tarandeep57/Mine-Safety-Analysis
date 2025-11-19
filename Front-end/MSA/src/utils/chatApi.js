import axios from 'axios';

const API_URL = 'http://127.0.0.1:5001/api';

export const getIncidents = async () => {
  try {
    const response = await axios.get(`${API_URL}/incidents`);
    return response.data;
  } catch (error) {
    console.error('Error fetching incidents:', error);
    throw error;
  }
};

export const getReports = async () => {
  try {
    const response = await axios.get(`${API_URL}/reports`);
    return response.data;
  } catch (error) {
    console.error('Error fetching reports:', error);
    throw error;
  }
};

export const getAlerts = async () => {
  try {
    const response = await axios.get(`${API_URL}/alerts`);
    return response.data;
  } catch (error) {
    console.error('Error fetching alerts:', error);
    throw error;
  }
};

export const sendMessage = async (message, history, onChunk) => {
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message, history }),
    });

    if (!response.body) {
      throw new Error("Response body is null");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullResponse = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      
      const chunk = decoder.decode(value, { stream: true });
      // SSE format is "data: {...}\n\n"
      const jsonStrings = chunk.match(/data: (.*)\n\n/g);

      if (jsonStrings) {
        for (const jsonString of jsonStrings) {
          try {
            const cleanJson = jsonString.replace(/^data: /, '').replace(/\n\n$/, '');
            const parsed = JSON.parse(cleanJson);
            
            if (parsed.end_of_stream) {
              return fullResponse;
            }
            
            if (parsed.text) {
              fullResponse += parsed.text;
              onChunk(parsed.text); // Callback to update UI with the new chunk
            }
          } catch (e) {
            console.error("Error parsing stream chunk:", e, "Chunk:", jsonString);
          }
        }
      }
    }
    return fullResponse; // Should be returned when the stream ends
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};
