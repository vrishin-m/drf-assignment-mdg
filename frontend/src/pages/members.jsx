import React, { useEffect, useState } from "react";


const AVAILABLE_ROLES = [
  "Studio Admin",
  "Project Lead",
  "Designer",
  "Writer",
  "Reviewer",
  "Client Viewer",
];

export default function UserRolesProjectsPage() {
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingUserId, setSavingUserId] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);

      const [usersRes, projectsRes] = await Promise.all([
        fetch("/api/users"),
        fetch("/api/projects"),
      ]);

      if (!usersRes.ok || !projectsRes.ok) {
        throw new Error("Failed to fetch data");
      }

      const usersData = await usersRes.json();
      const projectsData = await projectsRes.json();

      setUsers(usersData);
      setProjects(projectsData);
    } catch (err) {
      console.error(err);
      setError("Unable to load users or projects.");
    } finally {
      setLoading(false);
    }
  };

  const toggleRole = (userId, role) => {
    setUsers((prev) =>
      prev.map((user) => {
        if (user.id !== userId) return user;

        const hasRole = user.roles.includes(role);

        return {
          ...user,
          roles: hasRole
            ? user.roles.filter((r) => r !== role)
            : [...user.roles, role],
        };
      })
    );
  };

  const toggleProject = (userId, projectId) => {
    setUsers((prev) =>
      prev.map((user) => {
        if (user.id !== userId) return user;

        const hasProject = user.projects.includes(projectId);

        return {
          ...user,
          projects: hasProject
            ? user.projects.filter((p) => p !== projectId)
            : [...user.projects, projectId],
        };
      })
    );
  };

  const saveAssignments = async (user) => {
    try {
      setSavingUserId(user.id);

      const response = await fetch(
        `/api/users/${user.id}/assignments`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            roles: user.roles,
            projects: user.projects,
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to save");
      }

      alert(`Saved assignments for ${user.name}`);
    } catch (err) {
      console.error(err);
      alert("Failed to save assignments.");
    } finally {
      setSavingUserId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-lg font-medium">
        Loading users and projects...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-red-600 font-medium">
        {error}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">
          User Role & Project Management
        </h1>

        <div >
          {users.map((user) => (
            <div
              key={user.id}
              className="bg-white rounded-2xl shadow p-6"
            >
              {/* User Info */}
              <div>
                <h2>
                  {user.name}
                </h2>
                <p >{user.email}</p>
              </div>

              {/* Roles */}
              <div >
                <h3 >
                  Assign Roles
                </h3>

                <div >
                  {AVAILABLE_ROLES.map((role) => {
                    const selected = user.roles.includes(role);

                    return (
                      <button
                        key={role}
                        onClick={() =>
                          toggleRole(user.id, role)
                        }
                      
                      >
                        {role}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Projects */}
              <div >
                <h3 >
                  Assign Projects
                </h3>

                <div>
                  {projects.map((project) => {
                    const selected =
                      user.projects.includes(project.id);

                    return (
                      <label
                        key={project.id}
                        
                      >
                        <input
                          type="checkbox"
                          checked={selected}
                          onChange={() =>
                            toggleProject(
                              user.id,
                              project.id
                            )
                          }
                        />

                        <span>{project.name}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              {/* Save */}
              <div >
                <button
                  onClick={() => saveAssignments(user)}
                  disabled={savingUserId === user.id}
                  
                >
                  {savingUserId === user.id
                    ? "Saving..."
                    : "Save Assignments"}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}