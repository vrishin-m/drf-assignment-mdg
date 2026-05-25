import { useState, useEffect } from 'react';
import api from '../api';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { useParams } from 'react-router-dom';



const COLUMN_NAMES = ['draft', 'review', 'revision', 'approved', 'completed'];

export default function TaskBoard() {
  const { studioSlug, projectId } = useParams();
  const [data, setData] = useState({ tasks: {}, columns: {}, columnOrder: [] });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');


  useEffect(() => {
    const fetchProjectTasks = async () => {
      try {
        const url = `/studios/${studioSlug}/projects/${projectId}/tasks/`;
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
          const status = task.stage || 'draft';
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
        setMessage('Could not load tasks for this project.');
        setLoading(false);
      }
    };

    fetchProjectTasks();
  }, [studioSlug, projectId]); 



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
      const url = `/studios/${studioSlug}/projects/${projectId}/tasks/${draggableId}/transition/`;
      await api.post(url, { to_stage: destination.droppableId });
      
    } catch (err) {
      console.error("Failed to transition task:", err);

      setMessage('Failed to save task movement.');
    }
  };

  if (loading) return <div style={{ padding: '40px' }}>Loading Task Board...</div>;

  return (
    <div>
      {message && <div style={{ color: 'red', padding: '10px' }}>{message}</div>}
      
      <DragDropContext onDragEnd={onDragEnd}>
        <div style={{ display: 'flex', gap: '20px', padding: '20px', overflowX: 'auto', alignItems: 'flex-start' }}>
          
          {data.columnOrder.map((columnId) => {
            const column = data.columns[columnId];
            const tasks = column.taskIds.map((taskId) => data.tasks[taskId]);

            return (
              <div key={column.id} style={{ width: '300px', flexShrink: 0, background: '#f4f5f7', padding: '10px', borderRadius: '8px' }}>
                <h3 style={{ margin: '0 0 15px 0', color: '#172b4d', fontSize: '16px' }}>{column.title} <span style={{color: '#5e6c84', fontSize:'14px', fontWeight:'normal'}}>({tasks.length})</span></h3>
                
                <Droppable droppableId={column.id}>
                  {(provided) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.droppableProps}
                      style={{ minHeight: '200px', height: '100%' }}
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
                                marginBottom: '8px',
                                backgroundColor: 'white',
                                borderRadius: '4px',
                                boxShadow: '0 1px 2px rgba(9,30,66,0.25)',
                                ...provided.draggableProps.style,
                              }}
                            >
                              <strong style={{ display: 'block', marginBottom: '4px' }}>{task.title}</strong>
                              <div style={{ fontSize: '12px', color: '#666' }}>
                                Priority: {task.priority || 'Normal'}
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