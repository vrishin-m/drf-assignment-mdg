import { useState } from 'react';

// use npm install @hello-pangea/dnd to install lib before using this 
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { initialBoardData } from '../../frontend_testing/mockdata';

export default function TaskBoard() {
  const [data, setData] = useState(initialBoardData);
  const onDragEnd = (result) => {
    const { destination, source, draggableId } = result;

    if (!destination) return;
    if (
      destination.droppableId === source.droppableId &&
      destination.index === source.index
    ) {
      return;
    }

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

    // API CALL HERE
  };

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div style={{ display: 'flex', gap: '20px', padding: '20px', overflowX: 'auto' }}>
        {data.columnOrder.map((columnId) => {
          const column = data.columns[columnId];
          const tasks = column.taskIds.map((taskId) => data.tasks[taskId]);

          return (
            <div key={column.id} style={{ width: '300px', background: '#f4f5f7', padding: '10px', borderRadius: '8px' }}>
              <h3 style={{ margin: '0 0 15px 0' }}>{column.title}</h3>
              
              <Droppable droppableId={column.id}>
                {(provided) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    style={{ minHeight: '200px' }}
                  >
                    {tasks.map((task, index) => (
                      <Draggable key={task.id} draggableId={task.id} index={index}>
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
                              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                              ...provided.draggableProps.style,
                            }}
                          >
                            <strong>{task.title}</strong>
                            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                              Priority: {task.priority}
                            </div>
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {/* placeholder */}
                    {provided.placeholder}
                  </div>
                )}
              </Droppable>
            </div>
          );
        })}
      </div>
    </DragDropContext>
  );
}