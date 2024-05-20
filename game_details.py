import os
import random

import pandas as pd
import sqlite3 as s3
import uuid

# pd.set_option('display.max_columns', None)

class Database:
    def __init__(self, db_name):
        self.con = s3.connect(db_name)
        self.cursor = self.con.cursor()


db = Database('Game.db')


def create_unit_library():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'resources', 'Classes.csv'),
                     index_col=0)
    df = df.reset_index()
    df = df[df['FS'].str.isnumeric()]
    df['unit_type'] = df['Infantry'].str.split('\n').str[0]
    df['description'] = df['Infantry'].str.split('\n').str[1]
    df.drop(columns=['Infantry'], inplace=True)
    df.to_sql('unit_library', db.con, if_exists='replace', index=False)


class Units:
    def recruit(self, company_uuid, unit_name, unit_type):
        unit_details = pd.read_sql("SELECT * FROM unit_library WHERE unit_type = '{}'".format(unit_type), db.con)
        unit_details['id'] = str(uuid.uuid4())
        unit_details['company_uuid'] = company_uuid
        unit_details['unit_type'] = unit_type
        unit_details['unit_name'] = unit_name
        unit_details['start_pos_x'] = 1
        unit_details['start_pos_y'] = 1
        unit_details['start_orientation'] = 'N'
        unit_details['end_orientation'] = 'N'
        unit_details['end_pos_x'] = 1
        unit_details['end_pos_y'] = 1
        unit_details['status'] = 'Active'

        if len(self.by_name(unit_name))==0:
            unit_details.to_sql('units', db.con, if_exists='append', index=False)

    def list(self, active=True):
        df = pd.read_sql('SELECT * FROM units', db.con)
        if active:
            df = df[df['status'] == 'Active']
        return df

    def by_name(self, unit_name):
        df = pd.read_sql("SELECT * FROM units WHERE unit_name = '{}'".format(unit_name), db.con)
        return df

    def details(self, unit_id):
        df = pd.read_sql('SELECT * FROM units', db.con)
        df = df[df['id'] == unit_id][0]
        print(df)
        return df

    def default_unit_info(self, unit_name):
        df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'resources', 'Classes.csv'),
                         index_col=0)
        df = df.reset_index()
        df = df[df['FS'].str.isnumeric()]
        df['unit_name'] = df['Infantry'].str.split('\n').str[0]
        df['description'] = df['Infantry'].str.split('\n').str[1]
        print(df.head(5))
        unit = df[df['unit_name'] == unit_name].min()
        return unit.to_dict()

    def move(self, unit_name, dest_x, dest_y, dest_orientation):
        db.cursor.execute('''UPDATE units 
         SET start_pos_x = end_pos_x,
            start_pos_y = end_pos_y,
            start_orientation = end_orientation,
            end_pos_x = {},
            end_pos_y = {},
            end_orientation = '{}'
        WHERE unit_name = '{}'
         '''.format( dest_x, dest_y, dest_orientation,unit_name))
        db.con.commit()


class Companies:
    def add(self, company_name, discord_handle, dm_rights=False):
        df = pd.DataFrame(
            [{
                'id': str(uuid.uuid4()),
                'discord_handle': discord_handle,
                'company_name': company_name,
                'dm': dm_rights
            }]
        )
        if len(self.get_id_by_name('company_name'))==0:
            df.to_sql('companies', db.con, if_exists='append', index=False)

    def get_details_by_name(self, company_name):
        df = pd.read_sql("SELECT * FROM companies where company_name = '{}'".format(company_name), db.con)
        return df.min()

    def get_id_by_name(self, company_name):
        df = pd.read_sql("SELECT id FROM companies where company_name = '{}'".format(company_name), db.con)
        return df.min()

    def delete_company(self, uuid):
        db.cursor.execute('''DELETE FROM companies WHERE uuid = '{}' '''.format(uuid))
        db.con.commit()

    def list_companies(self):
        df = pd.read_sql('SELECT * FROM companies', db.con)
        return df


if __name__ == '__main__':
    companies = Companies()
    units = Units()
    create_unit_library()
    companies.add('Test Company', 'b33ps', True)
    companies.add('Bugs', 'b33ps', True)
    companies.add('Other', 'b33ps', True)
    for unit_num in range (15):
        units.recruit(companies.get_id_by_name('Test Company'), 'Test Unit {}'.format(unit_num), 'Combat Medical Unit')
    for unit_num in range (5):
        units.recruit(companies.get_id_by_name('Bugs'), 'Bug {}'.format(unit_num), 'Bug')
    for unit_num in range(5):
        units.recruit(companies.get_id_by_name('Other'), 'Other {}'.format(unit_num), 'UnknownIntel')


    for unit in units.list().to_dict('records'):
        rand_coord_x = random.randrange(2,20)
        rand_coord_y = random.randrange(2,20)
        if 'other' in unit['unit_name'].lower():
            o_list = ['N']
        else:
            o_list = ['N','S', 'E', 'W', 'SW', 'SE', 'NW', 'NE']
        rand_orientation = random.choice(o_list)
        units.move(unit['unit_name'], rand_coord_x, rand_coord_y, rand_orientation)
    print(units.list())
