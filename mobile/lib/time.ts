export const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export const newId = () => `${Date.now()}-${Math.random()}`;
