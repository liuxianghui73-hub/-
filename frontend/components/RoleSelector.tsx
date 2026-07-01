'use client';

import { ChatRole } from '@/types/chat';

interface RoleSelectorProps {
  currentRole: ChatRole;
  onRoleChange: (role: ChatRole) => void;
  disabled: boolean;
}

const ROLES: { value: ChatRole; label: string; icon: string; description: string }[] = [
  {
    value: 'sales',
    label: '销售话术生成',
    icon: '💼',
    description: '擅长撰写邮件、微信话术'
  },
  {
    value: 'competitor',
    label: '竞品分析',
    icon: '📊',
    description: '擅长 SWOT 分析、差异化对比'
  },
  {
    value: 'portrait',
    label: '客户画像',
    icon: '👤',
    description: '擅长根据碎片信息推断客户性格与决策偏好'
  }
];

export default function RoleSelector({ currentRole, onRoleChange, disabled }: RoleSelectorProps) {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newRole = e.target.value as ChatRole;
    onRoleChange(newRole);
  };

  return (
    <div className="flex items-center gap-3">
      <label htmlFor="role-select" className="text-sm text-gray-400 whitespace-nowrap">
        当前角色：
      </label>
      <select
        id="role-select"
        value={currentRole}
        onChange={handleChange}
        disabled={disabled}
        className="bg-gray-700 text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
      >
        {ROLES.map(role => (
          <option key={role.value} value={role.value}>
            {role.icon} {role.label}
          </option>
        ))}
      </select>
      <span className="text-xs text-gray-500 hidden md:inline">
        {ROLES.find(r => r.value === currentRole)?.description}
      </span>
    </div>
  );
}
