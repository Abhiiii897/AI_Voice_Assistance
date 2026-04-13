import { useState, useRef } from 'react';
import { Trash2, Pin } from 'lucide-react';
import useDashboardStore from '../../hooks/useDashboardStore';
import type { Note } from '../../types'; // Import the Note type

function NotesPanel() {
    //subscribe to notes and notes actions from Zustand store
    const notes = useDashboardStore((state) => state.notes);
    /*when useDashboardStore() is used if returns the entire store object,
    with all the state fields AND all the action fns
    e.g:  activeCallId: null,
          callStartTime: null,
          //and all other state fields
          and
          addNote: (text) => { ... },
          deleteNote: (id) => { ... },
          togglePinned: (id) => { ... },
          //all other action objects
    the '{ }' thing down is JS/TypeScript destructuring syntax
    it extracts the specific properties only from the entire object by name
          */
    //const { addNote, deleteNote, togglePinned } = useDashboardStore();
    //using useDashboardStore() without a selector like '((state))' subscribes the component to every state change, so it's better to use granular subscriptions
    //so for better clarity and performance:
    const addNote = useDashboardStore((state) => state.addNote);
    const deleteNote = useDashboardStore((state) => state.deleteNote);
    const togglePinned = useDashboardStore((state) => state.togglePinned);

    // Local state for input field
    //useState is a React hook that creates a state variable
    //a useState returns current value of state and a setter fn to update it, so setNewNoteText is the setter fn
    const [newNoteText, setNewNoteText] = useState('');

    // Ref to the scrollable container (for manual scroll control)
    // directly links via the reference to the scrollable container DOM Element,
    // useRef react hook makes a persistent container,the <HTMLDivElement> states 
    // that the useref will point to a <div> element and (null) is the int value
    // before the ref is mounted to an actual DOM at runtime 
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    // Handle adding a new note
    const handleAddNote = () => {
        if (newNoteText.trim()) { //.trim() == .strip() in python
            addNote(newNoteText); // Call Zustand action
            setNewNoteText('');   // Clear input
        }
    };

    // Separate pinned and regular notes
    const pinnedNotes = notes.filter((n) => n.isPinned);
    const regularNotes = notes.filter((n) => !n.isPinned);

    return (
        <div className="flex flex-col h-full">
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-700">
            <h2 className="font-bold text-sm">Agent Notes</h2>
            <p className="text-xs text-gray-500 mt-1">{notes.length} notes</p>
        </div>

        {/* Input Section */}
        <div className="px-4 py-3 border-b border-gray-700 flex-shrink-0">
            <div className="flex gap-2">
            <input
                type="text"
                value={newNoteText}
                onChange={(e) => setNewNoteText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
                placeholder="Add a note..."
                className="flex-1 bg-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            />
            <button
                onClick={handleAddNote}
                className="bg-blue-600 hover:bg-blue-700 p-2 rounded transition-colors flex-shrink-0"
                title="Add note"
            >
                <span className="text-white font-bold">+</span>
            </button>
            </div>
        </div>

        {/* Scrollable Notes List */}
        <div
            ref={scrollContainerRef}
            className="flex-1 overflow-y-auto px-4 py-4 space-y-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800"
        >
            {/* Pinned Notes (appear first) */}
            {pinnedNotes.map((note) => (
            <NoteItem
                key={note.id}
                note={note}
                onDelete={deleteNote}
                onTogglePin={togglePinned}
                isPinned={true}
            />
            ))}

            {/* Regular Notes */}
            {regularNotes.map((note) => (
            <NoteItem
                key={note.id}
                note={note}
                onDelete={deleteNote}
                onTogglePin={togglePinned}
                isPinned={false}
            />
            ))}

            {/* Empty State */}
            {notes.length === 0 && (
            <div className="text-gray-500 text-center py-8 text-sm">
                No notes yet. Add one to get started.
            </div>
            )}
        </div>
        </div>
    );
}

/**
 * Individual note item component
 * Shows note text, timestamp, and action buttons on hover
 */
interface NoteItemProps {
  readonly note: Note; 
  readonly onDelete: (id: string) => void;
  readonly onTogglePin: (id: string) => void;
  readonly isPinned: boolean;
}

function NoteItem({ note, onDelete, onTogglePin, isPinned }: NoteItemProps) {
  return (
    <div
      className={`p-3 rounded-lg text-sm transition-all group hover:shadow-md ${
        isPinned
          ? 'bg-yellow-500/20 border-l-2 border-yellow-500' //pinned colors
          : 'bg-gray-700/50 border-l-2 border-gray-600'   //unpinned colors
      }`}
    >
      {/* Note Content */}
      <div className="flex justify-between items-start gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-gray-200 break-words">{note.text}</p>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(note.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        </div>

        {/* Action Buttons (show on hover) */}
        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
          <button
            onClick={() => onTogglePin(note.id)}
            className="p-1 hover:bg-gray-600 rounded transition-colors text-yellow-400"
            title={isPinned ? 'Unpin note' : 'Pin note'}
          >
            <Pin className="w-3 h-3" />
          </button>
          <button
            onClick={() => onDelete(note.id)}
            className="p-1 hover:bg-red-600/30 rounded transition-colors text-red-400"
            title="Delete note"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default NotesPanel;