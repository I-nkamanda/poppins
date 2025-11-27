import React, { useState } from 'react';
import { setApiKey } from '../services/api';

interface ApiKeyModalProps {
    onConfigured: () => void;
}

export const ApiKeyModal: React.FC<ApiKeyModalProps> = ({ onConfigured }) => {
    const [apiKey, setKey] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            await setApiKey(apiKey);
            onConfigured();
        } catch (err) {
            setError('Failed to configure API Key. Please check the key and try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full">
                <h2 className="text-2xl font-bold mb-4">API Key Configuration</h2>
                <p className="mb-4 text-gray-600 text-sm">
                    Please enter your Google Gemini API Key to continue.
                    This key will be stored locally in your standalone app.
                </p>
                <form onSubmit={handleSubmit}>
                    <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setKey(e.target.value)}
                        placeholder="Enter Gemini API Key"
                        className="w-full p-2 border rounded mb-4 focus:ring-2 focus:ring-blue-500 outline-none"
                        required
                        minLength={20}
                    />
                    {error && <p className="text-red-500 mb-4 text-sm">{error}</p>}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                    >
                        {loading ? 'Configuring...' : 'Save API Key'}
                    </button>
                </form>
                <div className="mt-4 text-sm text-gray-500 text-center">
                    <a
                        href="https://aistudio.google.com/app/apikey"
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-600 hover:underline"
                    >
                        Get API Key from Google AI Studio
                    </a>
                </div>
            </div>
        </div>
    );
};
