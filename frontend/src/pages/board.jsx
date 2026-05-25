import { useState, useEffect } from 'react';
import api from '../api';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { useParams } from 'react-router-dom';

const COLUMN_NAMES = ['draft', 'review', 'revision', 'approved', 'completed'];

export default function TaskBoard() {
  const { studioSlug } = useParams();
  const [data, setData] = useState({ tasks: {}, columns: {}, columnOrder: [] });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchProjectTasks = async () => {
      if (!studioSlug) return;
      
      try {
        const url = `studios/${studioSlug}/tasks/`;
        const response = await api.get(url);
        const rawTasks = response.data;

        const initialData = {
          tasks: {},
          columns: {},
          columnOrder: COLUMN_NAMES,
        };

        COLUMN_NAMES.forEach((col) => {
          initialData.columns[col] = {
            id: col,
            title: col.charAt(0).toUpperCase() + col.slice(1),
            taskIds: [],
          };
        });

        rawTasks.forEach(task => {
          const status = (task.stage || 'draft').toLowerCase();
          initialData.tasks[task.id] = task;
          
          if (initialData.columns[status]) {
            initialData.columns[status].taskIds.push(task.id);
          } else {
            initialData.columns['draft'].taskIds.push(task.id);
          }
        });

        setData(initialData);
        setLoading(false);
      } catch (err) {
        console.error("Error fetching tasks:", err);
        setMessage('Could not load tasks for this studio workspace workflow.');
        setLoading(false);
      }
    };

    fetchProjectTasks();
  }, [studioSlug]); 

  const onDragEnd = async (result) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;

    const startColumn = data.columns[source.droppableId];
    const finishColumn = data.columns[destination.droppableId];

    if (startColumn === finishColumn) {
      const newTaskIds = Array.from(startColumn.taskIds);
      newTaskIds.splice(source.index, 1);
      newTaskIds.splice(destination.index, 0, draggableId);

      const newColumn = { ...startColumn, taskIds: newTaskIds };
      setData({
        ...data,
        columns: { ...data.columns, [newColumn.id]: newColumn },
      });
      return;
    }

    const startTaskIds = Array.from(startColumn.taskIds);
    startTaskIds.splice(source.index, 1);
    const newStartColumn = { ...startColumn, taskIds: startTaskIds };

    const finishTaskIds = Array.from(finishColumn.taskIds);
    finishTaskIds.splice(destination.index, 0, draggableId);
    const newFinishColumn = { ...finishColumn, taskIds: finishTaskIds };

    setData({
      ...data,
      columns: {
        ...data.columns,
        [newStartColumn.id]: newStartColumn,
        [newFinishColumn.id]: newFinishColumn,
      },
    });

    try {
      const url = `studios/${studioSlug}/tasks/${draggableId}/transition/`;
      await api.post(url, { to_stage: destination.droppableId });
    } catch (err) {
      console.error("Failed to transition task stage:", err);
      setMessage('Failed to synchronize status movement with backend.');
    }
  };

  if (loading) return <div style={{ padding: '40px', color: '#cbd5e0' }}>Loading Workflow Task Board...</div>;

  return (
    <div style={{ minHeight: '100vh', padding: '80px 20px 20px 20px' }}>
      {message && (
        <div style={{ color: '#fff', backgroundColor: '#e53e3e', padding: '12px 16px', borderRadius: '6px', marginBottom: '20px', fontSize: '14px', maxWidth: '600px' }}>
          {message}
        </div>
      )}
      
      <DragDropContext onDragEnd={onDragEnd}>
        <div style={{ display: 'flex', gap: '20px', overflowX: 'auto', alignItems: 'flex-start', paddingBottom: '20px' }}>
          
          {data.columnOrder.map((columnId) => {
            const column = data.columns[columnId];
            const tasks = column.taskIds
              .map((taskId) => data.tasks[taskId])
              .filter(task => task !== undefined);

            return (
              <div key={column.id} style={{ width: '280px', flexShrink: 0, background: '#1a202c', padding: '16px', borderRadius: '8px', border: '1px solid #2d3748' }}>
                <h3 style={{ margin: '0 0 15px 0', color: '#e2e8f0', fontSize: '15px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {column.title} <span style={{ color: '#718096', fontSize: '13px', fontWeight: 'normal' }}>({tasks.length})</span>
                </h3>
                
                <Droppable droppableId={column.id}>
                  {(provided) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      style={{ minHeight: '300px', width: '100%' }}
                    >
                      {tasks.map((task, index) => (
                        <Draggable key={String(task.id)} draggableId={String(task.id)} index={index}>
                          {(provided) => (
                            <div
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              {...provided.dragHandleProps}
                              style={{
                                padding: '16px',
                                marginBottom: '10px',
                                backgroundColor: '#2d3748',
                                borderRadius: '6px',
                                border: '1px solid #4a5568',
                                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
                                cursor: 'grab',
                                ...provided.draggableProps.style,
                              }}
                            >
                              <strong style={{ display: 'block', marginBottom: '8px', color: '#f7fafc', fontSize: '14px' }}>{task.title}</strong>
                              {task.description && <p style={{ fontSize: '13px', color: '#a0aec0', margin: '0 0 10px 0', lineHeight: '1.4' }}>{task.description}</p>}
                              <div style={{ fontSize: '11px', color: '#cbd5e0', textTransform: 'uppercase', fontWeight: 'bold', display: 'inline-block', backgroundColor: '#1a202c', padding: '2px 8px', borderRadius: '4px' }}>
                                ⚡ {task.priority || 'Medium'}
                              </div>
                            </div>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </div>
                  )}
                </Droppable>
              </div>
            );
          })}
          
        </div>
      </DragDropContext>
    </div>
  );
}