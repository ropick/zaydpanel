import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function PATCH(request: NextRequest) {
  try {
    const { name, email } = await request.json();

    // Find admin user and update
    const admin = await db.user.findFirst({ where: { role: 'admin' } });
    if (!admin) {
      return NextResponse.json({ success: false, message: 'Admin tidak ditemukan' }, { status: 404 });
    }

    const updated = await db.user.update({
      where: { id: admin.id },
      data: { name, email },
    });

    return NextResponse.json({ success: true, user: updated });
  } catch (error) {
    console.error('Admin profile error:', error);
    return NextResponse.json({ success: false, message: 'Server error' }, { status: 500 });
  }
}
