import React, { useState } from 'react';
import { useWindowStore, useUIStore } from '@/stores';

interface LessonCreatorWindowProps {
    windowId: string;
    componentProps?: Record<string, unknown>;
}

interface LessonConfig {
    topic: string;
    detailLevel: 'beginner' | 'intermediate' | 'advanced';
    useInternet: boolean;
}

export const LessonCreatorWindow: React.FC<LessonCreatorWindowProps> = ({ windowId }) => {
    const { openWindow, closeWindow } = useWindowStore();
    const { addNotification } = useUIStore();

    const [config, setConfig] = useState<LessonConfig>({
        topic: '',
        detailLevel: 'intermediate',
        useInternet: true,
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!config.topic.trim()) {
            addNotification({
                title: 'Error',
                message: 'Please enter a topic to learn about',
                type: 'error',
            });
            return;
        }

        setIsSubmitting(true);

        try {
            // Call the teaching API
            const response = await fetch('/api/lessons', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: config.topic,
                    detail_level: config.detailLevel,
                    use_internet: config.useInternet,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to create lesson');
            }

            const data = await response.json();
            const lessonId = data.id;
            console.log('[TeachingCrew] Lesson created:', data);

            // Close creator and open viewer
            closeWindow(windowId);
            openWindow({
                id: `lesson-viewer-${lessonId}`,
                title: `📚 Lesson: ${config.topic.slice(0, 30)}...`,
                icon: '📚',
                component: 'lesson-viewer',
                componentProps: { lessonId },
            });

            addNotification({
                title: 'Lesson Started',
                message: `Generating lesson: ${config.topic}`,
                type: 'success',
            });
        } catch (error) {
            console.error('[TeachingCrew] Failed to create lesson:', error);
            addNotification({
                title: 'Error',
                message: 'Failed to connect to backend. Make sure the server is running on port 5040.',
                type: 'error',
            });
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="p-4 h-full flex flex-col">
            <form onSubmit={handleSubmit} className="flex flex-col gap-4 flex-1">
                {/* Topic Input */}
                <div className="flex flex-col gap-1">
                    <label className="text-sm font-bold">What would you like to learn about?</label>
                    <textarea
                        className="xp-input w-full h-[80px] resize-none"
                        placeholder="Enter a topic (e.g., Quantum Computing, History of Rome, Climate Change)..."
                        value={config.topic}
                        onChange={(e) => setConfig({ ...config, topic: e.target.value })}
                    />
                </div>

                {/* Detail Level */}
                <fieldset className="border-2 border-gray-300 p-3 rounded">
                    <legend className="px-2 text-sm font-bold">Detail Level</legend>
                    <div className="flex gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="radio"
                                name="level"
                                checked={config.detailLevel === 'beginner'}
                                onChange={() => setConfig({ ...config, detailLevel: 'beginner' })}
                            />
                            <span className="text-sm">🌱 Beginner</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="radio"
                                name="level"
                                checked={config.detailLevel === 'intermediate'}
                                onChange={() => setConfig({ ...config, detailLevel: 'intermediate' })}
                            />
                            <span className="text-sm">📖 Intermediate</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="radio"
                                name="level"
                                checked={config.detailLevel === 'advanced'}
                                onChange={() => setConfig({ ...config, detailLevel: 'advanced' })}
                            />
                            <span className="text-sm">🎓 Advanced</span>
                        </label>
                    </div>
                </fieldset>

                {/* Options */}
                <fieldset className="border-2 border-gray-300 p-3 rounded">
                    <legend className="px-2 text-sm font-bold">Research Options</legend>
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            className="xp-checkbox"
                            checked={config.useInternet}
                            onChange={(e) => setConfig({ ...config, useInternet: e.target.checked })}
                        />
                        <span className="text-sm">Enable internet research</span>
                    </label>
                </fieldset>

                {/* Info Box */}
                <div className="bg-purple-50 border border-purple-200 p-3 rounded text-xs">
                    <p className="font-bold text-purple-800 mb-1">📚 Teaching Mode</p>
                    <p className="text-purple-600">
                        The AI teacher will research the topic and create a structured lesson
                        with key concepts, examples, and review questions.
                    </p>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-2 mt-auto pt-4 border-t border-gray-300">
                    <button
                        type="button"
                        className="xp-button px-6"
                        onClick={() => closeWindow(windowId)}
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        className="xp-button px-6"
                        disabled={isSubmitting || !config.topic.trim()}
                    >
                        {isSubmitting ? 'Creating...' : 'Start Lesson'}
                    </button>
                </div>
            </form>
        </div>
    );
};
