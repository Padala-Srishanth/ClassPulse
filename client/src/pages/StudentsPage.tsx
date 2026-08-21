import React, { useEffect, useState } from 'react';
import { ArrowRight, Filter, GraduationCap, Search, Sparkles, Users } from 'lucide-react';
import { RiskBadge } from '../components/RiskBadge';
import { useAuth } from '../context/AuthContext';
import { classesApi } from '../api/classes';
import { studentsApi } from '../api/students';
import { riskApi } from '../api/risk';
import { RiskAlert, RiskLevel, SchoolClass, Student } from '../types';

interface StudentsPageProps {
  onSelectStudent: (studentId: string) => void;
  onOpenIntervention: (student: Student) => void;
}

export const StudentsPage: React.FC<StudentsPageProps> = ({
  onSelectStudent,
  onOpenIntervention,
}) => {
  const { schoolId } = useAuth();
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [selectedClassId, setSelectedClassId] = useState<string>('');
  const [students, setStudents] = useState<Student[]>([]);
  const [alertsMap, setAlertsMap] = useState<Record<string, RiskAlert>>({});
  const [search, setSearch] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadClasses() {
      if (!schoolId) return;
      try {
        const clsList = await classesApi.listSchoolClasses(schoolId);
        setClasses(clsList);
        if (clsList.length > 0) {
          setSelectedClassId(clsList[0].id);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadClasses();
  }, [schoolId]);

  useEffect(() => {
    async function loadStudentsAndAlerts() {
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
    }
    loadStudentsAndAlerts();
  }, [selectedClassId]);

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
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>Student Directory & Risk Tracking</h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Monitor engagement indicators and historical risk levels per student.
          </p>
        </div>

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
              placeholder="Search by student name or student ID..."
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
                <th>Student Code</th>
                <th>Student Name</th>
                <th>Grade / Section</th>
                <th>Risk Status</th>
                <th>Primary Indicator</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredStudents.map((stu) => {
                const alert = alertsMap[stu.id];
                const riskLevel: RiskLevel = alert ? alert.risk_level : 'LOW';
                const score = alert ? alert.risk_score : undefined;
                const reasonText = alert?.reasons[0]?.explanation || 'Engagement stable';

                return (
                  <tr key={stu.id}>
                    <td style={{ fontWeight: 600, color: '#475569', fontSize: '0.82rem' }}>
                      {stu.student_code}
                    </td>
                    <td style={{ fontWeight: 700, color: '#0f172a' }}>
                      {stu.name}
                    </td>
                    <td>
                      {stu.grade} - {stu.section}
                    </td>
                    <td>
                      <RiskBadge level={riskLevel} score={score} />
                    </td>
                    <td style={{ fontSize: '0.82rem', color: '#475569', maxWidth: '300px' }}>
                      {reasonText}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '8px' }}>
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
