import React, { useEffect, useState } from 'react';
import { ArrowRight, Edit3, Filter, GraduationCap, Phone, Plus, Search, UserCheck } from 'lucide-react';
import { RiskBadge } from '../components/RiskBadge';
import { useAuth } from '../context/AuthContext';
import { classesApi } from '../api/classes';
import { studentsApi } from '../api/students';
import { riskApi } from '../api/risk';
import { calculateAcademicGrade } from '../utils/grading';
import { RiskAlert, RiskLevel, SchoolClass, Student } from '../types';


interface StudentsPageProps {
  onSelectStudent: (studentId: string) => void;
  onOpenIntervention: (student: Student) => void;
  onOpenEditStudent?: (student: Student) => void;
  onOpenCreateStudent?: () => void;
  onOpenAttendance?: (classId: string, className: string, students: Student[]) => void;
}

export const StudentsPage: React.FC<StudentsPageProps> = ({
  onSelectStudent,
  onOpenIntervention,
  onOpenEditStudent,
  onOpenCreateStudent,
  onOpenAttendance,
}) => {
  const { schoolId } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<string>('');
  const [students, setStudents] = useState<Student[]>([]);
  const [alertsMap, setAlertsMap] = useState<Record<string, RiskAlert>>({});
  const [search, setSearch] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  const loadClasses = async () => {
    if (!schoolId) return;
    try {
      const clsList = await classesApi.listSchoolClasses(schoolId);
      setClasses(clsList);
      if (clsList.length > 0 && !selectedClassId) {
        setSelectedClassId(clsList[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadStudentsAndAlerts = async () => {
    if (!selectedClassId) return;
    setLoading(true);
    try {
      const [stuList, activeAlerts] = await Promise.all([
        studentsApi.listClassStudents(selectedClassId),
        riskApi.getClassActiveAlerts(selectedClassId),
      ]);
      setStudents(stuList);

      const aMap: Record<string, RiskAlert> = {};
      activeAlerts.forEach((a) => {
        aMap[a.student_id] = a;
      });
      setAlertsMap(aMap);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClasses();
  }, [schoolId]);

  useEffect(() => {
    if (classes.length > 0 && (!selectedClassId || !classes.some((c) => c.id === selectedClassId))) {
      setSelectedClassId(classes[0].id);
    }
  }, [classes, selectedClassId]);

  useEffect(() => {
    loadStudentsAndAlerts();
  }, [selectedClassId]);

  const selectedClassObj = classes.find((c) => c.id === selectedClassId);
  const selectedClassName = selectedClassObj ? selectedClassObj.name : 'Class';

  const filteredStudents = students.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.student_code.toLowerCase().includes(search.toLowerCase());

    const alert = alertsMap[s.id];
    const riskLevel: RiskLevel = alert ? alert.risk_level : 'LOW';

    if (filterRisk === 'ALL') return matchesSearch;
    if (filterRisk === 'HIGH') return matchesSearch && riskLevel === 'HIGH';
    if (filterRisk === 'MEDIUM') return matchesSearch && riskLevel === 'MEDIUM';
    if (filterRisk === 'LOW') return matchesSearch && riskLevel === 'LOW';
    if (filterRisk === 'INSUFFICIENT_DATA') return matchesSearch && riskLevel === 'INSUFFICIENT_DATA';
    return matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Student Directory & Attendance</h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Manage student records, edit profiles, and submit daily class attendance sheets.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          {classes.length > 0 && (
            <select
              className="form-select"
              style={{ width: 'auto', fontWeight: 600 }}
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
            >
              {classes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.grade}-{c.section})
                </option>
              ))}
            </select>
          )}

          {onOpenAttendance && (
            <button
              className="btn btn-outline"
              onClick={() => onOpenAttendance(selectedClassId, selectedClassName, students)}
              disabled={students.length === 0}
            >
              <UserCheck size={16} color="#16a34a" />
              Take Attendance
            </button>
          )}

          {onOpenCreateStudent && (
            <button className="btn btn-primary" onClick={onOpenCreateStudent}>
              <Plus size={16} />
              Enroll Student
            </button>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: '240px' }}>
            <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '12px' }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '36px' }}
              placeholder="Search by student name or student code..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Filter size={16} color="#64748b" />
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>Filter:</span>
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
              <button
                key={lvl}
                className={`btn btn-sm ${filterRisk === lvl ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setFilterRisk(lvl)}
              >
                {lvl === 'ALL' ? 'All Students' : lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Students Data Table */}
      <div className="table-container">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
            Loading students...
          </div>
        ) : filteredStudents.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
            No students found matching current filters.
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Roll No</th>
                <th>Student & Contact</th>
                <th>Class</th>
                <th>Status</th>
                <th>Exam Grade</th>
                <th>Risk Level</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.map((stu) => {
                const alert = alertsMap[stu.id];
                const riskLevel: RiskLevel = alert ? alert.risk_level : 'LOW';
                const score = alert ? alert.risk_score : undefined;
                
                // Determine exam grade from test signals or risk score
                const testReason = alert?.reasons?.find((r) => r.metric?.includes('test') || r.signal_type === 'TEST_SCORE');
                const testVal = testReason ? testReason.current_value : (alert ? (100 - alert.risk_score) / 100 : 0.88);
                const gradeInfo = calculateAcademicGrade(testVal !== undefined && testVal !== null ? testVal * 100 : null);


                return (
                  <tr key={stu.id}>
                    <td style={{ fontWeight: 600, color: '#475569', fontSize: '0.82rem' }}>
                      {stu.student_code}
                    </td>
                    <td>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>{stu.name}</div>
                      {stu.parent_contact ? (
                        <div style={{ fontSize: '0.75rem', color: '#6366f1', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                          <Phone size={11} /> {stu.parent_contact}
                        </div>
                      ) : (
                        <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>No contact</div>
                      )}
                    </td>
                    <td>
                      Grade {stu.grade}-{stu.section}
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '6px',
                          background: stu.status === 'ACTIVE' ? '#dcfce7' : '#f1f5f9',
                          color: stu.status === 'ACTIVE' ? '#15803d' : '#64748b',
                        }}
                      >
                        {stu.status}
                      </span>
                    </td>
                    <td>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          background: gradeInfo.bgColor,
                          color: gradeInfo.color,
                          fontWeight: 700,
                          fontSize: '0.8rem',
                        }}
                      >
                        {gradeInfo.grade} <span style={{ fontSize: '0.7rem', opacity: 0.8 }}>({gradeInfo.label})</span>
                      </span>
                    </td>
                    <td>
                      <RiskBadge level={riskLevel} score={score} />
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '6px' }}>
                        {onOpenEditStudent && (
                          <button
                            className="btn btn-outline btn-sm"
                            onClick={() => onOpenEditStudent(stu)}
                            title="Edit student details"
                            style={{ padding: '6px 8px' }}
                          >
                            <Edit3 size={13} />
                          </button>
                        )}
                        <button
                          className="btn btn-outline btn-sm"
                          onClick={() => onOpenIntervention(stu)}
                          title="Record intervention"
                        >
                          <GraduationCap size={14} />
                          Intervene
                        </button>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => onSelectStudent(stu.id)}
                        >
                          Profile
                          <ArrowRight size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>

          </table>
        )}
      </div>
    </div>
  );
};
